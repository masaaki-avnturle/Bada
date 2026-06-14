package com.bada.silenttalk;

import android.media.Image;

import androidx.annotation.NonNull;
import androidx.camera.core.ExperimentalGetImage;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.core.ImageProxy;

import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.face.Face;
import com.google.mlkit.vision.face.FaceDetection;
import com.google.mlkit.vision.face.FaceDetector;
import com.google.mlkit.vision.face.FaceDetectorOptions;

import java.util.List;

/**
 * Turns front-camera frames into Silent Talk signals using on-device ML Kit face
 * detection:
 * <ul>
 *   <li><b>視線追跡 (gaze)</b> — head yaw/pitch (Euler angles) steer the cursor.</li>
 *   <li><b>表情 (expression)</b> — a deliberate blink = "select"; a smile = "home".</li>
 * </ul>
 * All processing is on-device; no frames leave the phone.
 */
class FaceGazeAnalyzer implements ImageAnalysis.Analyzer {

    interface Listener {
        void onGaze(float dx, float dy, float quality);
        void onBlink();
        void onSmile();
        void onFaceLost();
    }

    private final FaceDetector detector;
    private final Listener listener;

    private boolean eyesClosedPending = false;
    private long lastBlink = 0, lastSmile = 0;

    FaceGazeAnalyzer(Listener listener) {
        this.listener = listener;
        FaceDetectorOptions opts = new FaceDetectorOptions.Builder()
                .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_FAST)
                .setClassificationMode(FaceDetectorOptions.CLASSIFICATION_MODE_ALL)
                .build();
        detector = FaceDetection.getClient(opts);
    }

    @ExperimentalGetImage
    @Override
    public void analyze(@NonNull ImageProxy proxy) {
        Image media = proxy.getImage();
        if (media == null) {
            proxy.close();
            return;
        }
        InputImage image = InputImage.fromMediaImage(
                media, proxy.getImageInfo().getRotationDegrees());
        detector.process(image)
                .addOnSuccessListener(this::onFaces)
                .addOnFailureListener(e -> { /* drop frame */ })
                .addOnCompleteListener(t -> proxy.close());
    }

    private void onFaces(List<Face> faces) {
        if (faces.isEmpty()) {
            listener.onFaceLost();
            return;
        }
        Face f = faces.get(0);

        // Head pose -> gaze direction. Front camera is mirrored, so flip yaw.
        float yaw = f.getHeadEulerAngleY();   // left/right
        float pitch = f.getHeadEulerAngleX();  // up/down
        float dx = clamp(-yaw / 22f);
        float dy = clamp(-pitch / 18f);
        listener.onGaze(dx, dy, 1.0f);

        Float lE = f.getLeftEyeOpenProbability();
        Float rE = f.getRightEyeOpenProbability();
        Float sm = f.getSmilingProbability();
        long now = System.currentTimeMillis();

        if (lE != null && rE != null) {
            boolean closed = lE < 0.25f && rE < 0.25f;
            boolean open = lE > 0.6f && rE > 0.6f;
            if (closed) {
                eyesClosedPending = true;
            } else if (open && eyesClosedPending) {
                eyesClosedPending = false;
                if (now - lastBlink > 600) {
                    lastBlink = now;
                    listener.onBlink();
                }
            }
        }
        if (sm != null && sm > 0.7f && now - lastSmile > 1500) {
            lastSmile = now;
            listener.onSmile();
        }
    }

    private static float clamp(float v) {
        return v < -1f ? -1f : (v > 1f ? 1f : v);
    }
}

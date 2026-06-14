package com.bada.silenttalk;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.view.accessibility.AccessibilityEvent;

/**
 * Executes the device operations that Silent Talk "speaks" silently.
 *
 * <p>This is the same mechanism Voice Access uses: an {@link AccessibilityService}
 * with gesture dispatch, so taps / swipes / global navigation can be performed on
 * behalf of a user who cannot touch or speak.
 */
public class SilentTalkAccessibilityService extends AccessibilityService {

    private static SilentTalkAccessibilityService instance;

    public static SilentTalkAccessibilityService get() {
        return instance;
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
    }

    @Override
    public void onDestroy() {
        if (instance == this) instance = null;
        super.onDestroy();
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) { /* not needed */ }

    @Override
    public void onInterrupt() { }

    // -- operations --------------------------------------------------------
    public void tap(float x, float y) {
        Path p = new Path();
        p.moveTo(x, y);
        GestureDescription.StrokeDescription stroke =
                new GestureDescription.StrokeDescription(p, 0, 60);
        dispatchGesture(new GestureDescription.Builder().addStroke(stroke).build(), null, null);
    }

    public void swipe(float x1, float y1, float x2, float y2, long durationMs) {
        Path p = new Path();
        p.moveTo(x1, y1);
        p.lineTo(x2, y2);
        GestureDescription.StrokeDescription stroke =
                new GestureDescription.StrokeDescription(p, 0, Math.max(50, durationMs));
        dispatchGesture(new GestureDescription.Builder().addStroke(stroke).build(), null, null);
    }

    public void back()      { performGlobalAction(GLOBAL_ACTION_BACK); }
    public void home()      { performGlobalAction(GLOBAL_ACTION_HOME); }
    public void recents()   { performGlobalAction(GLOBAL_ACTION_RECENTS); }
    public void notifications() { performGlobalAction(GLOBAL_ACTION_NOTIFICATIONS); }
}

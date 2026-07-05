plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.masaaki.bada.iq"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.masaaki.bada.iq"
        minSdk = 26
        targetSdk = 34
        versionCode = 4
        versionName = "1.3"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    // Ship the Bada-language engine (bada_ruby/lib/bada_src/*.bada) as assets,
    // copied from the single source of truth so the two stay in sync.
    sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/bada_assets"))
}

val copyBadaAssets by tasks.registering(Copy::class) {
    from(rootProject.file("../bada_ruby/lib/bada_src")) { include("*.bada") }
    into(layout.buildDirectory.dir("generated/bada_assets"))
}

tasks.named("preBuild") { dependsOn(copyBadaAssets) }

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
}

<div align="center">
  <h1>🚀 CodePing-Android</h1>
  <p><em>Your ultimate companion for competitive programming, tracking contests, and mastering your coding journey.</em></p>
  
  <!-- Main Technology Stack Badges -->
  <img src="https://img.shields.io/badge/Platform-Android-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Android Platform">
  <img src="https://img.shields.io/badge/Language-Kotlin-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white" alt="Kotlin Language">
  <img src="https://img.shields.io/badge/UI-Jetpack%20Compose-4285F4?style=for-the-badge&logo=JetpackCompose&logoColor=white" alt="Jetpack Compose UI">
  <img src="https://img.shields.io/badge/Backend-Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase Backend">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="MIT License">
  
  <br><br>
  
  <!-- Quick action buttons for enhanced UX -->
  <a href="#introduction">📖 Overview</a> •
  <a href="#features">✨ Features</a> •
  <a href="#architecture">🏗️ Architecture</a> •
  <a href="#getting-started">🚀 Get Started</a>
</div>

<hr>

## 📖 Introduction

CodePing-Android is an enterprise-grade mobile application meticulously crafted to empower competitive programmers and coding enthusiasts. Designed with a strong emphasis on intuitive UI/UX and robust technical architecture, CodePing serves as a central hub for tracking contests, monitoring progress across various coding platforms, and managing user profiles.

This client application leverages the power of Kotlin and Jetpack Compose to deliver a fluid and delightful user experience, backed by Firebase for secure authentication and data management. Whether you're a seasoned competitive programmer or just starting your journey, CodePing-Android provides the tools you need to stay on top of your game and showcase your achievements.

## ✨ Key Features

CodePing-Android is packed with features designed to enhance your competitive programming experience:

*   **Seamless Onboarding Experience:** A beautifully designed, multi-page onboarding flow introduces users to CodePing's core functionalities, making first-time usage effortless and engaging. (See: [OnboardingScreen.kt](app/src/main/java/com/codeping/android_client/presentation/onboarding/OnboardingScreen.kt), [WelcomeScreen.kt](app/src/main/java/com/codeping/android_client/presentation/onboarding/screens/WelcomeScreen.kt), [FeaturesScreen.kt](app/src/main/java/com/codeping/android_client/presentation/onboarding/screens/FeaturesScreen.kt), [PlatformsScreen.kt](app/src/main/java/com/codeping/android_client/presentation/onboarding/screens/PlatformsScreen.kt))
*   **Robust Authentication System:** Securely sign in using popular social providers like Google and GitHub, powered by Firebase Authentication, ensuring a seamless and reliable login experience. (See: [AuthScreen.kt](app/src/main/java/com/codeping/android_client/presentation/auth/AuthScreen.kt), [AuthRepository.kt](app/src/main/java/com/codeping/android_client/data/auth/AuthRepository.kt))
*   **Dynamic Main Dashboard:** A personalized home screen provides quick access to essential information and navigation, acting as your command center for competitive programming. (See: [MainDashboardScreen.kt](app/src/main/java/com/codeping/android_client/ui/screens/MainDashboardScreen.kt))
*   **Intuitive Bottom Navigation:** A custom-designed bottom navigation bar with subtle animations ensures smooth transitions between core sections: Home, Contests, Share, Stats, and Profile. (See: [CodePingBottomNavigation.kt](app/src/main/java/com/codeping/android_client/ui/navigation/CodePingBottomNavigation.kt), [BottomNavItem.kt](app/src/main/java/com/codeping/android_client/ui/navigation/BottomNavItem.kt))
*   **Adaptive Theming:** Switch effortlessly between Light and Dark themes, offering a comfortable viewing experience day or night. The theme preference is persisted for continuity. (See: [ThemeManager.kt](app/src/main/java/com/codeping/android_client/ui/theme/ThemeManager.kt), [ThemeSwitcher.kt](app/src/main/java/com/codeping/android_client/ui/components/ThemeSwitcher.kt))
*   **Secure Data Persistence:** Sensitive user information and preferences are securely stored using AndroidX Security Crypto's `EncryptedSharedPreferences`, ensuring data privacy and integrity. (See: [SecurePreferences.kt](app/src/main/java/com/codeping/android_client/utils/SecurePreferences.kt))
*   **Comprehensive Error Logging:** An integrated error logging utility captures and stores detailed logs, aiding in robust error reporting and debugging. (See: [ErrorLogger.kt](app/src/main/java/com/codeping/android_client/utils/ErrorLogger.kt))
*   **Platform Tracking & Analytics (Planned):** Designed to track progress and stats across major competitive programming platforms like LeetCode, CodeChef, and Codeforces.
*   **Smart Contest Notifications (Planned):** Receive personalized alerts for upcoming contests on your favorite platforms.
*   **Shareable Profile Links (Planned):** Easily share your coding achievements with a beautiful, custom profile link.

## 🏗️ Architecture

CodePing-Android adopts a clean, modular architecture centered around the **MVVM (Model-View-ViewModel)** pattern, enhanced by Jetpack Compose's reactive UI paradigm. This separation of concerns ensures maintainability, testability, and scalability.

### Project Structure
The project is organized into logical modules and packages, promoting modularity and clear responsibilities:

```
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/codeping/android_client/
│   │   │   │   ├── data/            # Data Layer: Repositories, data sources (Firebase, APIs), data models
│   │   │   │   │   ├── auth/        # Authentication related data handling
│   │   │   │   ├── presentation/    # Presentation Layer: UI (Composables) and their respective ViewModels
│   │   │   │   │   ├── auth/        # Authentication UI and ViewModel
│   │   │   │   │   ├── main/        # Main dashboard UI
│   │   │   │   │   ├── onboarding/  # Onboarding UI and ViewModel
│   │   │   │   ├── ui/              # UI specific components (reusable UI elements, themes, navigation)
│   │   │   │   │   ├── components/  # Generic UI components
│   │   │   │   │   ├── navigation/  # Navigation definitions and custom UI
│   │   │   │   │   ├── screens/     # Root composable screens for navigation
│   │   │   │   │   ├── theme/       # Application wide theming (colors, typography, theme manager)
│   │   │   │   ├── utils/           # Utility classes (secure preferences, error logging)
│   │   │   │   ├── MainActivity.kt  # Main entry point and activity-level concerns (e.g., auth callbacks)
│   │   │   ├── AndroidManifest.xml  # Application manifest, permissions, activities
│   │   │   ├── res/                 # Android resources (layouts, drawables, values, mipmaps)
│   │   ├── androidTest/             # Instrumented tests for Android devices
│   │   ├── test/                    # Local unit tests
│   ├── build.gradle                 # Module-level Gradle build script
│   └── proguard-rules.pro           # ProGuard/R8 rules for code shrinking and obfuscation
└── gradle.properties                # Project-wide Gradle settings
```

### Data Flow & State Management

<details>
  <summary>Click to expand Data Flow details</summary>
  
  The application follows a unidirectional data flow within the MVVM pattern:
  
  1.  **View (Jetpack Composables):** Observes `StateFlow` from the `ViewModel` to reactively update the UI. It sends user interactions (events) to the `ViewModel`.
  2.  **ViewModel:** Contains UI state and business logic. It exposes `MutableStateFlow` (or other State Holders) that the View observes. It interacts with the `Repository` to fetch or update data. `AuthViewModel.kt` is a prime example of managing authentication state.
  3.  **Repository:** Abstracts data sources. It's responsible for fetching data from the network (APIs), local storage (SecurePreferences), or other services (Firebase). `AuthRepository.kt` handles authentication logic and interacts with Firebase.
  4.  **Data Sources:** Actual implementations for data retrieval and storage (e.g., `FirebaseAuth`, `GoogleSignInClient`, `SecurePreferences`).
  
  Jetpack Compose's `remember` and `collectAsStateWithLifecycle` are used for efficient state observation and lifecycle awareness, ensuring UI updates are performed safely and effectively.
</details>

### Navigation & Routing

Navigation within the app is primarily handled by Jetpack Compose Navigation, enabling declarative UI definitions and managing the back stack. The `MainDashboardScreen.kt` acts as the root of the authenticated navigation graph, hosting various feature screens. Initial routing from the splash screen (via `MainActivity.kt`) determines whether to show onboarding, authentication, or the main dashboard.

`MainActivity.kt` plays a crucial role in handling external authentication callbacks (e.g., Google Sign-In `ActivityResultContracts.StartActivityForResult`) and integrating them back into the `AuthViewModel` and `AuthRepository` flow.

## 💻 Technology Stack

CodePing-Android is built upon a robust and modern technology stack:

*   **Platform:** Android (API 21+)
*   **Language:** Kotlin
*   **UI Toolkit:** Jetpack Compose
*   **Build System:** Gradle
*   **Backend & Authentication:** Firebase (Firebase Authentication, Google Sign-In, OAuth for GitHub)
*   **Data Security:** AndroidX Security Crypto (`EncryptedSharedPreferences`)
*   **Browser Integration:** Chrome Custom Tabs (for GitHub OAuth flow)
*   **Testing:** JUnit, AndroidX Test (Espresso, UI Automator)

## 🚀 Getting Started

Follow these steps to get CodePing-Android up and running on your local development environment.

### Prerequisites

*   **Android Studio:** Version Giraffe (2022.3.1) or newer is recommended.
*   **Java Development Kit (JDK):** Version 17 or newer.
*   **Android SDK:** Target SDK Version 34 (Android 14) and Minimum SDK Version 21 (Android 5.0).
*   **Git:** For cloning the repository.
*   **Google Account:** Required for Firebase setup.
*   **GitHub Account:** Required for GitHub OAuth setup.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/gowtham-2oo5/CodePing-Android.git
    cd CodePing-Android
    ```
2.  **Open in Android Studio:**
    *   Launch Android Studio.
    *   Select `File` > `Open` and navigate to the cloned `CodePing-Android` directory.
    *   Allow Gradle to sync the project and download all necessary dependencies. This may take some time.

### Configuration

CodePing-Android relies on Firebase for authentication. You'll need to set up a Firebase project and configure it for your Android application.

1.  **Create a Firebase Project:**
    *   Go to the [Firebase Console](https://console.firebase.google.com/).
    *   Click `Add project` and follow the on-screen instructions to create a new project.
2.  **Add Android App to Firebase:**
    *   In your Firebase project, click the Android icon (<img src="https://www.gstatic.com/devrel-devsite/prod/vc3d162f1c841e06e788ee590a98f7e7a8e7a68595567b57954564c78103c8374/firebase/images/touchicon-180.png" width="16" height="16" alt="Firebase Icon">) to add an Android app.
    *   **Android package name:** `com.codeping.android_client`
    *   **App nickname:** (Optional, e.g., `CodePing Android Client`)
    *   **Debug signing certificate SHA-1:**
        *   Open Android Studio, navigate to `Gradle` tab (usually on the right).
        *   Click `app` > `Tasks` > `android` > `signingReport`.
        *   Look for the `SHA1` under `debug` variant. Copy this value.
        *   Paste the SHA-1 into the Firebase console.
    *   Register your app.
3.  **Download `google-services.json`:**
    *   Follow the Firebase instructions to download the `google-services.json` file.
    *   Place this file into your `app/` module directory:
        <kbd>CodePing-Android/app/google-services.json</kbd>
4.  **Enable Authentication Methods:**
    *   In the Firebase Console, go to `Authentication` > `Sign-in method`.
    *   Enable **Google** sign-in:
        *   Toggle enabled.
        *   Select a support email.
    *   Enable **GitHub** sign-in:
        *   Toggle enabled.
        *   You will need to provide a **GitHub Client ID** and **Client Secret**. Obtain these by creating a new OAuth App in your GitHub Developer Settings:
            *   Go to [GitHub Developer Settings](https://github.com/settings/developers).
            *   Click `New OAuth App`.
            *   **Application name:** `CodePing-Android` (or similar)
            *   **Homepage URL:** `https://github.com/gowtham-2oo5/CodePing-Android` (or your preferred URL)
            *   **Authorization callback URL:** <kbd>codeping://github-auth</kbd>
            *   Register the application to get your Client ID and Client Secret.
        *   **Important:** Replace `"your_github_client_id_here"` in [GitHubAuthHelper.kt](app/src/main/java/com/codeping/android_client/data/auth/GitHubAuthHelper.kt) with your actual GitHub Client ID. The Client Secret should be handled securely on a backend server, but for client-side testing, it might be used directly or indirectly via Firebase.

### Running the Application

After successful configuration and Gradle sync:

1.  Connect an Android device or start an Android Emulator.
2.  In Android Studio, click the `Run 'app'` button (green triangle icon) in the toolbar.

The application will build and install on your selected device/emulator.

## 📐 Project-Specific Settings

*   **Gradle Properties:**
    *   `org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8`: Configures JVM arguments for the Gradle daemon, allocating 2GB of memory and setting file encoding.
    *   `android.useAndroidX=true`: Ensures the project uses AndroidX libraries, the successor to the original Support Library.
    *   `kotlin.code.style=official`: Enforces the official Kotlin code style.
    *   `android.nonTransitiveRClass=true`: Improves build performance by namespacing R classes, reducing their size.
*   **ProGuard/R8 Rules:** The `app/proguard-rules.pro` file contains rules for code shrinking, obfuscation, and optimization. Currently, it includes commented-out examples for WebView JS interfaces and line number retention for debugging. Further rules may be added for production builds.

## 🔒 Data Persistence & Security

CodePing-Android prioritizes user data security.

*   **Secure User Data:** `SecurePreferences.kt` leverages `EncryptedSharedPreferences` from AndroidX Security Crypto. This ensures sensitive user information such as User ID, Email, Name, Photo URL, and Authentication Provider are stored encrypted on the device, protecting them from unauthorized access.
*   **Standard Preferences:** Less sensitive application preferences, such as onboarding completion status and theme selection, are stored using standard `SharedPreferences` (e.g., in [OnboardingViewModel.kt](app/src/main/java/com/codeping/android_client/presentation/onboarding/OnboardingViewModel.kt) and [ThemeManager.kt](app/src/main/java/com/codeping/android_client/ui/theme/ThemeManager.kt)).

## 🎨 Theming & UI/UX

As Best UI/UX Designer of the year, I've ensured CodePing-Android delivers a visually stunning and highly intuitive user experience.

*   **Material Design 3:** The application is built upon Google's Material Design 3 guidelines, providing a modern and accessible UI.
*   **Custom Color Palette:** A carefully curated color scheme defined in [Color.kt](app/src/main/java/com/codeping/android_client/ui/theme/Color.kt) uses `Emerald Green` as the primary brand accent, complemented by neutral backgrounds and clear status indicators (Success, Error, Warning, Info).
*   **Custom Typography:** `CodePingTypography` in [Type.kt](app/src/main/java/com/codeping/android_client/ui/theme/Type.kt) defines a clean and readable font hierarchy. While `MontserratFontFamily` is set to `FontFamily.Default` for system font fallback, custom Montserrat font assets can be easily integrated for a distinct brand aesthetic.
*   **Adaptive Theming:** The `ThemeManager.kt` provides seamless runtime toggling between `CodePingLightColorScheme` and `CodePingDarkColorScheme`, ensuring a comfortable experience in any lighting condition. The `ThemeSwitcher.kt` component offers a visually appealing way for users to control this.
*   **Animated Interactions:** Subtle yet impactful animations are integrated throughout the UI, from the tracing line in the bottom navigation to content transitions and theme switching, enhancing user engagement and perceived responsiveness.

## 🧪 Testing

The project includes basic test setups to ensure functional correctness.

*   **Unit Tests:** Located in `app/src/test/java`, these tests focus on isolated logic units. `ExampleUnitTest.kt` provides a basic example.
*   **Instrumented Tests:** Located in `app/src/androidTest/java`, these tests run on an Android device or emulator and can interact with the Android framework. `ExampleInstrumentedTest.kt` demonstrates how to test application context and package name.

Further comprehensive testing (UI tests with Espresso/Compose Testing, integration tests, and more extensive unit tests) would be implemented as the project matures, following a test-driven development approach.

---

## 🎉 Conclusion

CodePing-Android represents a commitment to delivering a high-quality, user-centric mobile application for the competitive programming community. Built with modern Android technologies—Kotlin, Jetpack Compose, and Firebase—it offers a robust, secure, and delightful experience for tracking contests, monitoring progress, and connecting with the coding world. The architectural patterns ensure scalability and maintainability, paving the way for continuous feature development.

### 🌟 What's Next?
The roadmap for CodePing-Android is exciting:
*   [ ] Real-time contest tracking and reminders with deep platform integration.
*   [ ] Advanced performance analytics and visualization across user profiles.
*   [ ] Personalizable shareable profile links.
*   [ ] Community features and direct challenges.
*   [ ] Further UI/UX enhancements and animations.

### 🤝 Contributing
We welcome contributions from the community to make CodePing-Android even better! Please consider:
1.  Forking the repository.
2.  Creating a feature branch (`git checkout -b feature/your-feature-name`).
3.  Making your changes and committing them (`git commit -m 'feat: Add amazing new feature'`).
4.  Pushing to your branch (`git push origin feature/your-feature-name`).
5.  Opening a pull request with a clear description of your changes.

### 📞 Support & Contact
-   🐛 Issues: Please report any bugs or issues you encounter directly on [GitHub Issues](https://github.com/gowtham-2oo5/CodePing-Android/issues).
-   💬 Questions: For general questions or discussions, feel free to open a discussion or reach out via GitHub.

---

<div align="center">
  <strong>⭐ Star this repo if you find it helpful or inspiring!</strong>
  <br>
  <em>Made with ❤️ for the global developer community</em>
</div>
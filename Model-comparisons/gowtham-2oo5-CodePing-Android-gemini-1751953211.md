<div align="center">
  <h1>🚀 CodePing-Android</h1>
  <p><em>Your ultimate companion for competitive programming – track contests, monitor stats, and elevate your coding journey with a beautiful, modern Android app.</em></p>

  <!-- MAIN TECH STACK & PROJECT STATUS BADGES -->
  <p>
    <img src="https://img.shields.io/badge/Kotlin-0095D5?style=for-the-badge&logo=kotlin&logoColor=white" alt="Kotlin">
    <img src="https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Android">
    <img src="https://img.shields.io/badge/Jetpack%20Compose-4285F4?style=for-the-badge&logo=jetpackcompose&logoColor=white" alt="Jetpack Compose">
    <img src="https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase">
    <img src="https://img.shields.io/badge/Material%20Design%203-7B1FA2?style=for-the-badge&logo=materialdesign&logoColor=white" alt="Material Design 3">
    <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License">
    <img src="https://img.shields.io/github/stars/gowtham-2oo5/CodePing-Android?style=for-the-badge&color=blueviolet" alt="GitHub Stars">
    <img src="https://img.shields.io/github/forks/gowtham-2oo5/CodePing-Android?style=for-the-badge&color=blueviolet" alt="GitHub Forks">
  </p>

  <br>

  <!-- Quick action buttons -->
  <p>
    <a href="#installation">🚀 Get Started</a> •
    <a href="#features">✨ Features</a> •
    <a href="#architecture">🏗️ Architecture</a> •
    <a href="#contributing">🤝 Contribute</a>
  </p>
</div>

<hr>

## 📖 Table of Contents
<details>
  <summary>Click to expand</summary>
  <ol>
    <li><a href="#about-codeping-android">🌟 About CodePing-Android</a></li>
    <li><a href="#features">✨ Features</a></li>
    <li><a href="#architecture-and-design">🏗️ Architecture and Design</a>
      <ul>
        <li><a href="#architectural-pattern">Architectural Pattern</a></li>
        <li><a href="#project-structure">Project Structure</a></li>
        <li><a href="#data-flow-and-state-management">Data Flow and State Management</a></li>
        <li><a href="#navigation">Navigation</a></li>
      </ul>
    </li>
    <li><a href="#technology-stack">💻 Technology Stack</a></li>
    <li><a href="#installation-and-setup">🛠️ Installation and Setup</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#clone-the-repository">Clone the Repository</a></li>
        <li><a href="#firebase-project-setup">Firebase Project Setup</a></li>
        <li><a href="#github-oauth-configuration">GitHub OAuth Configuration</a></li>
        <li><a href="#run-the-application">Run the Application</a></li>
      </ul>
    </li>
    <li><a href="#configuration">⚙️ Configuration</a></li>
    <li><a href="#testing">🧪 Testing</a></li>
    <li><a href="#troubleshooting">💡 Troubleshooting</a></li>
    <li><a href="#contributing">🤝 Contributing</a></li>
    <li><a href="#conclusion">🎉 Conclusion</a></li>
  </ol>
</details>

---

## 🌟 About CodePing-Android

CodePing-Android is a cutting-edge mobile application built to empower competitive programmers. It serves as a centralized hub for tracking contests, monitoring performance metrics across various platforms, and securely managing user data. Designed with a strong emphasis on modern UI/UX principles, the app offers a smooth, intuitive experience for coders to stay on top of their game.

The application leverages the power of Kotlin and Jetpack Compose to deliver a native Android experience, featuring secure authentication via Google and GitHub, an interactive onboarding flow, and dynamic theming.

**Our mission:** To provide competitive programmers with a reliable, feature-rich, and beautifully designed tool that simplifies their tracking needs and keeps them motivated.

---

## ✨ Features

CodePing-Android is packed with thoughtful features designed to enhance the competitive programming experience:

*   **Secure Authentication:**
    *   Seamless sign-in with **Google** for quick access.
    *   Robust **GitHub OAuth** integration using custom tabs for secure code-based authentication.
    *   Leverages **Firebase Authentication** for backend user management.
*   **Intuitive Onboarding Experience:**
    *   A multi-page onboarding flow introduces users to the app's core value propositions, including a welcome message, key features overview, and supported platforms.
    *   `WelcomeScreen` with branding and tagline.
    *   `FeaturesScreen` highlighting "Smart Contest Notifications", "Comprehensive Stats Tracking", and "Easy Profile Sharing".
    *   `PlatformsScreen` showcasing support for **LeetCode**, **CodeChef**, and **Codeforces**, with a "Coming Soon" section for future integrations.
*   **Dynamic Theme Switching:**
    *   Toggle between **Light** and **Dark** themes with a dedicated in-app switcher.
    *   Theme preference is persisted securely using `EncryptedSharedPreferences`.
*   **Modern UI/UX:**
    *   Built entirely with **Jetpack Compose** following **Material Design 3** guidelines for a visually appealing and consistent interface.
    *   Custom-designed, animated **Bottom Navigation Bar** for a delightful user experience with `Home`, `Contests`, `Share`, `Stats`, and `Profile` sections.
    *   Splash screen integration for a polished app launch experience.
*   **Secure Data Storage:**
    *   User authentication data and preferences are securely stored using `AndroidX Security EncryptedSharedPreferences`, ensuring sensitive information is protected.
*   **Comprehensive Error Logging:**
    *   An internal `ErrorLogger` utility captures detailed application errors, including timestamps, locations, user journeys, and stack traces, writing them to a local log file for debugging and analysis.

---

## 🏗️ Architecture and Design

CodePing-Android follows a modern, modular architecture to ensure maintainability, scalability, and testability.

### Architectural Pattern
The project primarily adheres to the **MVVM (Model-View-ViewModel)** architectural pattern, widely adopted for Android development with Jetpack Compose.

*   **View (`presentation` package):** Composable functions (e.g., `AuthScreen`, `MainScreen`, `OnboardingScreen`, `MainDashboardScreen`) are responsible for rendering the UI and observing changes in the ViewModel's state. They expose events (like button clicks) to the ViewModel.
*   **ViewModel (`presentation` package):** Classes like `AuthViewModel` and `OnboardingViewModel` manage UI-related state and logic. They act as a bridge between the View and the Model, exposing `StateFlow` streams that the UI observes. They do not hold direct references to Views to prevent memory leaks and maintain separation of concerns.
*   **Model/Data Layer (`data` package):** Consists of repositories (`AuthRepository`) and utility classes (`GitHubAuthHelper`, `SecurePreferences`). This layer is responsible for data retrieval, storage, and business logic. It abstracts away the data sources (e.g., Firebase, local preferences) from the ViewModels.

### Project Structure
The repository is organized into a clean, feature-driven structure:

```
CodePing-Android/
├── app/
│   ├── src/
│   │   ├── androidTest/  # Instrumented tests
│   │   │   └── java/
│   │   │       └── com/codeping/android_client/ExampleInstrumentedTest.kt
│   │   ├── main/
│   │   │   ├── AndroidManifest.xml   # Application manifest
│   │   │   ├── java/
│   │   │   │   └── com/codeping/android_client/
│   │   │   │       ├── data/         # Data layer: repositories, data sources
│   │   │   │       │   └── auth/     # Authentication specific data handling
│   │   │   │       │       ├── AuthRepository.kt
│   │   │   │       │       └── GitHubAuthHelper.kt
│   │   │   │       ├── presentation/ # Feature-specific UI logic and Composables
│   │   │   │       │   ├── auth/     # Authentication screens and ViewModel
│   │   │   │       │   │   ├── AuthScreen.kt
│   │   │   │       │   │   └── AuthViewModel.kt
│   │   │   │       │   ├── main/     # Main dashboard screen
│   │   │   │       │   │   └── MainScreen.kt
│   │   │   │       │   └── onboarding/ # Onboarding screens and ViewModel
│   │   │   │       │       ├── components/ # Reusable onboarding UI components
│   │   │   │       │       ├── screens/    # Individual onboarding pages
│   │   │   │       │       ├── OnboardingPreviews.kt
│   │   │   │       │       ├── OnboardingScreen.kt
│   │   │   │       │       └── OnboardingViewModel.kt
│   │   │   │       ├── ui/           # Global UI elements: theme, navigation, shared screens
│   │   │   │       │   ├── components/   # Reusable UI components
│   │   │   │       │   ├── navigation/   # Bottom navigation structure
│   │   │   │       │   ├── screens/      # Main dashboard hosts (e.g., MainDashboardScreen)
│   │   │   │       │   └── theme/        # Material Design 3 theme definitions
│   │   │   │       │       ├── Color.kt
│   │   │   │       │       ├── Theme.kt
│   │   │   │       │       ├── ThemeManager.kt
│   │   │   │       │       └── Type.kt
│   │   │   │       │   └── MainActivity.kt     # Main application entry point
│   │   │   │       └── utils/        # Utility classes: error logging, secure preferences
│   │   │   │           ├── ErrorLogger.kt
│   │   │   │           └── SecurePreferences.kt
│   │   │   └── res/        # Android resources (layouts, drawables, values, etc.)
│   │   └── test/           # Unit tests
│   │       └── java/
│   │           └── com/codeping/android_client/ExampleUnitTest.kt
│   ├── proguard-rules.pro  # ProGuard/R8 rules for code shrinking and obfuscation
│   └── build.gradle        # Module-level Gradle build script
├── gradle/
│   └── wrapper/
│       └── gradle-wrapper.properties
├── build.gradle            # Project-level Gradle build script
└── gradle.properties       # Global Gradle settings
```

### Data Flow and State Management
The application leverages Jetpack Compose's reactive UI paradigm:
*   **Unidirectional Data Flow:** UI events (clicks, input) flow from the View to the ViewModel.
*   **State Observation:** ViewModels expose UI state using `kotlinx.coroutines.flow.StateFlow`, which Composables observe using `collectAsStateWithLifecycle()`. This ensures efficient updates and lifecycle awareness.
*   **Lifecycle Awareness:** `LaunchedEffect` and `collectAsStateWithLifecycle` are used to manage side effects and state collection in a lifecycle-safe manner.

### Navigation
Navigation within CodePing-Android is handled using Jetpack Compose Navigation:
*   **`NavHost`:** The central navigation component in `MainDashboardScreen.kt` defines the navigation graph and manages the back stack.
*   **Bottom Navigation:** A custom, animated `CodePingBottomNavigation` provides primary navigation between `Home`, `Contests`, `Share`, `Stats`, and `Profile` sections, each mapping to a unique route.
*   **Conditional Navigation:** `MainActivity` orchestrates the initial navigation flow, directing users to the `OnboardingScreen`, `AuthScreen`, or `MainScreen` based on their onboarding and authentication status, ensuring a tailored first-run experience.

---

## 💻 Technology Stack

*   **Primary Language:** Kotlin
*   **Mobile Platform:** Android
*   **UI Framework:** Jetpack Compose (Modern Android UI Toolkit)
*   **Design System:** Material Design 3
*   **Build System:** Gradle
*   **Authentication:** Firebase Authentication (for Google Sign-In, GitHub OAuth)
*   **Identity Providers:** Google Sign-In, GitHub OAuth
*   **Secure Storage:** AndroidX Security (EncryptedSharedPreferences)
*   **Concurrency:** Kotlin Coroutines & Flows
*   **Testing Frameworks:** JUnit, AndroidX Test (AndroidJUnit4)
*   **Development Tools:** Android Studio

---

## 🛠️ Installation and Setup

Follow these steps to get CodePing-Android up and running on your local machine.

### Prerequisites

*   **Android Studio:** Latest stable version (e.g., Flamingo or higher).
*   **Android SDK:** API Level 34 (or highest supported by Android Studio).
*   **Git:** Version control system.
*   **Physical Android Device or Emulator:** With Google Play services installed (for Google Sign-In).
*   **Firebase Project:** A Firebase project configured for Android, with Google Sign-In and GitHub as authentication providers enabled.
*   **GitHub OAuth App:** A GitHub OAuth application configured with the correct redirect URI.

### Clone the Repository

First, clone the CodePing-Android repository to your local machine:

```bash
git clone https://github.com/gowtham-2oo5/CodePing-Android.git
cd CodePing-Android
```

### Firebase Project Setup

1.  **Create a Firebase Project:** Go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.
2.  **Add Android App:**
    *   In your Firebase project, click "Add app" and select the Android icon.
    *   Enter the `Android package name`: `com.codeping.android_client` (found in `app/src/main/AndroidManifest.xml`).
    *   Enter the `App nickname`: `CodePing Android Client` (or your preferred name).
    *   Generate a **SHA-1 fingerprint**:
        *   In Android Studio, open your project.
        *   On the right side of the IDE, click on "Gradle".
        *   Navigate to `app` -> `Tasks` -> `android` -> `signingReport`.
        *   Double-click `signingReport` to run it. The SHA-1 fingerprint will appear in the "Run" window.
        *   Copy the SHA-1 fingerprint and paste it into the Firebase console.
    *   Register your app.
3.  **Download `google-services.json`:** Download the `google-services.json` file provided by Firebase and place it in the `app/` directory of your Android Studio project.
4.  **Enable Authentication Methods:**
    *   In the Firebase Console, navigate to `Authentication` -> `Sign-in method`.
    *   Enable **Google** sign-in: Follow the instructions provided, ensuring your support email is configured.
    *   Enable **GitHub** sign-in:
        *   You will need to provide your GitHub OAuth **Client ID** and **Client Secret**. (See next section for obtaining these).
        *   Firebase will provide a redirect URI (e.g., `https://<YOUR_FIREBASE_PROJECT_ID>.firebaseapp.com/__/auth/handler`). You will need to add this to your GitHub OAuth app's callback URLs.

### GitHub OAuth Configuration

1.  **Create a GitHub OAuth App:**
    *   Go to your GitHub `Settings` -> `Developer settings` -> `OAuth Apps` -> `New OAuth App`.
    *   **Application name:** `CodePing Android Client` (or similar).
    *   **Homepage URL:** `https://github.com/gowtham-2oo5/CodePing-Android` (or your project's homepage).
    *   **Authorization callback URL:**
        *   Add `codeping://github-auth` (defined in `app/src/main/java/com/codeping/android_client/data/auth/GitHubAuthHelper.kt`).
        *   Also add the Firebase OAuth redirect URI you obtained in the Firebase setup step (e.g., `https://<YOUR_FIREBASE_PROJECT_ID>.firebaseapp.com/__/auth/handler`).
    *   Register the application.
2.  **Obtain Client ID and Secret:** After creating the app, GitHub will provide you with a `Client ID` and allow you to generate a `Client Secret`. **Copy these immediately.**
3.  **Update `GitHubAuthHelper.kt`:**
    *   Open `app/src/main/java/com/codeping/android_client/data/auth/GitHubAuthHelper.kt`.
    *   Replace `"your_github_client_id_here"` with your actual GitHub OAuth **Client ID**:
        ```kotlin
        private const val GITHUB_CLIENT_ID = "YOUR_ACTUAL_GITHUB_CLIENT_ID" // Replace this
        ```
    *   **Important:** The `Client Secret` is handled by Firebase and is not stored in the client-side code for security reasons.

### Run the Application

1.  **Open in Android Studio:** Open the cloned `CodePing-Android` project in Android Studio.
2.  **Sync Gradle:** Allow Gradle to sync the project and download dependencies.
3.  **Select Device:** Choose an Android emulator or a physical device.
4.  **Run:** Click the `Run 'app'` button (green triangle) in Android Studio.

The application should now build and launch on your selected device.

---

## ⚙️ Configuration

The primary configuration points for CodePing-Android are:

*   **Firebase Integration:** As detailed in the Firebase Setup, ensure your `google-services.json` is correctly placed and authentication methods are enabled in the Firebase console.
*   **GitHub OAuth Client ID:** The `GITHUB_CLIENT_ID` in `app/src/main/java/com/codeping/android_client/data/auth/GitHubAuthHelper.kt` must be replaced with your actual Client ID obtained from GitHub.
*   **ProGuard/R8 Rules:** The `app/proguard-rules.pro` file contains standard rules for code shrinking and obfuscation. For release builds, you might need to add specific rules to prevent obfuscation of classes required by reflection or specific SDKs.
*   **JVM Arguments for Gradle:** `gradle.properties` sets `org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8` to optimize Gradle's JVM memory usage during builds.
*   **Android API Levels:**
    *   The `AndroidManifest.xml` indicates `tools:targetApi="31"`, suggesting the app is designed to run on Android 12 (API 31) and higher, leveraging features like the new Splash Screen API.
    *   Minimum API level is typically defined in `build.gradle`, ensuring broader compatibility.

---

## 🧪 Testing

CodePing-Android includes a basic setup for automated testing.

*   **Unit Tests (`app/src/test/`):**
    *   Small, fast tests that verify the logic of individual components (e.g., utility functions, ViewModel logic) in isolation without needing an Android device or emulator.
    *   Example: `app/src/test/java/com/codeping/android_client/ExampleUnitTest.kt`
*   **Instrumented Tests (`app/src/androidTest/`):**
    *   Tests that run on a real device or emulator, verifying UI interactions, database operations, and other functionalities that require an Android environment.
    *   Example: `app/src/androidTest/java/com/codeping/android_client/ExampleInstrumentedTest.kt` checks the application context.

To run tests:
*   **Unit Tests:** In Android Studio, navigate to `app/src/test/java`, right-click on the test file or directory, and select `Run Tests`.
*   **Instrumented Tests:** Ensure an emulator or device is connected. Navigate to `app/src/androidTest/java`, right-click on the test file or directory, and select `Run Tests`.

---

## 💡 Troubleshooting

Here are some common issues and their solutions:

*   **`google-services.json` not found or incorrect:**
    *   **Symptom:** Build errors related to Firebase, or app crashes on launch when interacting with Firebase.
    *   **Solution:** Ensure `google-services.json` is placed directly in the `app/` module directory. Verify that the `package_name` in `google-services.json` matches `com.codeping.android_client` exactly. Re-download and replace if unsure.
*   **Firebase Authentication Errors (Google/GitHub):**
    *   **Symptom:** Sign-in fails with "Google sign-in failed" or "GitHub authentication failed" messages in Logcat.
    *   **Solution:**
        *   **Google:** Double-check that your SHA-1 fingerprint is correctly registered in the Firebase project settings for your Android app.
        *   **GitHub:** Ensure your `GITHUB_CLIENT_ID` in `GitHubAuthHelper.kt` is correct. Verify that `codeping://github-auth` and the Firebase redirect URI are correctly added to your GitHub OAuth app's "Authorization callback URLs."
        *   Check Firebase Console -> Authentication -> Sign-in method to ensure Google and GitHub providers are enabled.
*   **Gradle Sync Failures:**
    *   **Symptom:** Android Studio shows "Gradle sync failed" errors.
    *   **Solution:**
        *   Check your internet connection.
        *   Ensure your Android Studio and Gradle Plugin versions are compatible.
        *   Try `File -> Invalidate Caches / Restart...` in Android Studio.
        *   Increase Gradle's JVM memory by adjusting `org.gradle.jvmargs=-Xmx2048m` in `gradle.properties` if you suspect memory issues.
*   **UI Not Updating/State Issues:**
    *   **Symptom:** Composables don't react to state changes, or display incorrect data.
    *   **Solution:** Ensure you are observing `StateFlow`s correctly using `collectAsStateWithLifecycle()`. Verify that state updates are happening on the main thread (Coroutines handle this well with `Dispatchers.Main`).
*   **App Crash on Launch (Splash Screen/Edge-to-Edge):**
    *   **Symptom:** App crashes immediately after splash screen, or UI elements are cut off.
    *   **Solution:** Ensure `SplashScreen.Companion.installSplashScreen()` is called **before** `super.onCreate()` in `MainActivity.kt`. Verify theme configurations, especially if you're targeting older Android versions that might not fully support the latest splash screen or edge-to-edge APIs without proper compatibility libraries.
*   **Cannot access logs on device:**
    *   **Symptom:** Debug logs are not visible in Logcat, or you can't find the custom error log file.
    *   **Solution:** For Logcat, ensure your filter is set correctly (e.g., `TAG` from `ErrorLogger` like `CodePing_ErrorLogger`). For the custom log file, you can access it via Device File Explorer in Android Studio: `data/data/com.codeping.android_client/files/codeping_errors.log`.

If you encounter persistent issues, please create a detailed GitHub Issue.

---

## 🤝 Contributing

We warmly welcome contributions to CodePing-Android! Your help is invaluable in making this project even better.

To contribute:
1.  **Fork** the repository on GitHub.
2.  **Clone** your forked repository to your local machine.
3.  Create a new **feature branch** for your changes:
    ```bash
    git checkout -b feature/your-feature-name
    ```
4.  Make your desired **changes** and ensure all tests pass.
5.  **Commit** your changes with clear, concise commit messages.
6.  **Push** your branch to your forked repository.
7.  Open a **Pull Request** to the `main` branch of the original CodePing-Android repository.

Please ensure your code adheres to Kotlin coding conventions and follows the existing architectural patterns. Provide clear descriptions of your changes in the pull request.

---

## 🎉 Conclusion

CodePing-Android stands as a testament to modern Android development, leveraging Kotlin and Jetpack Compose to deliver a performant, beautiful, and user-centric application. Built with a solid MVVM architecture and Material Design 3, it offers competitive programmers a powerful tool for tracking their progress and contests across major platforms like LeetCode, CodeChef, and Codeforces, all while prioritizing security and user experience.

### 🌟 What's Next?
We envision CodePing evolving into the quintessential platform for competitive programmers. Future plans include:
*   [ ] Real-time contest tracking and notifications with richer details.
*   [ ] Advanced statistics and visualization of user performance.
*   [ ] Enhanced profile sharing features and community integrations.
*   [ ] Support for more competitive programming platforms.

Community contributions, feedback, and suggestions are highly encouraged as we build out these exciting features.

### 🤝 Contributing
We believe in open collaboration and invite you to join us in shaping the future of CodePing. Whether it's reporting bugs, suggesting new features, or contributing code, every effort makes a difference.

### 📞 Support & Contact
*   🐛 **Issues:** Please report any bugs or issues you encounter via GitHub Issues.
*   💬 **Questions:** Feel free to open a discussion on GitHub for general queries or suggestions.

---

<div align="center">
  <strong>⭐ Star this repo if you find it helpful or interesting!</strong>
  <br>
  <em>Made with ❤️ for the developer community</em>
</div>
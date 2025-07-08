**README GENERATION PROMPT: CodePing-Server**

**Objective:** Generate a professional, comprehensive, and developer-friendly README for the `CodePing-Server` backend application.

**Project Context:**

*   **Project Name:** CodePing-Server (artifact: `Core-Server`)
*   **Repository:** `https://github.com/gowtham-2oo5/CodePing-Server`
*   **Primary Function:** A Spring Boot backend service designed to aggregate and manage competitive programming data from various online judges, coupled with internal user management and potential AI-driven insights.

**Technical Stack:**

*   **Backend Framework:** Java 17, Spring Boot 3.x (Spring Web, Spring WebFlux, Spring Data JPA)
*   **Data Persistence:** JPA for relational database interaction
*   **Caching:** Redis (Spring Data Redis)
*   **API Documentation:** OpenAPI 3 (Swagger UI) via `springdoc-openapi-starter-webmvc-ui`
*   **External API Integration:** Reactive `WebClient` for LeetCode, Codeforces, and a local CodeChef microservice
*   **Rate Limiting:** Implemented using `Bucket4j`
*   **Utilities:** Lombok, Project Reactor
*   **AI Integration:** Spring AI (dependency `spring-ai-bom`)

**Key Features & Functionality:**

*   **Internal User Management:** Full CRUD operations for `CodePing` platform users
*   **Competitive Programming Data Aggregation:**
    *   Fetch user profiles, contest history, ratings graphs, and recent submissions from external APIs
    *   Data parsed and mapped from external API responses into internal models
*   **Robustness & Performance:** Centralized global exception handling, efficient data retrieval and storage, API rate limiting
*   **Scheduled Operations:** Background tasks for data synchronization or maintenance
*   **Profile Sharing:** Generate and share aggregated user performance profiles

**Getting Started:**

1.  **Prerequisites:**
    *   Java 17+
    *   Maven
    *   Running Redis instance
2.  **Configuration:**
    *   Set up database connection properties (e.g., in `application.properties`)
    *   Configure API keys for external APIs (LeetCode, Codeforces, CodeChef if external)
3.  **Running:**
    *   Run the Spring Boot application using the standard command: `mvn spring-boot:run`
4.  **Swagger UI:**
    *   Access API documentation at: `/swagger-ui.html`

**API Endpoints Overview:**

*   `/api/v1/users`: Full CRUD operations for internal user management
*   `/profile/{username}`: Fetch user profile from external APIs
*   `/ratings/{username}`: Fetch ratings graph from external APIs
*   `/contest-history/{username}`: Fetch contest history from external APIs
*   `/recent-submissions/{username}`: Fetch recent submissions from external APIs

**Database Schema:**

*   **CPUsers**: Representing internal users
*   **PlatformUser**: Mapping external user profiles to internal users
*   **AIReview**: Potential AI-driven insights or feedback generation
*   **ProfileShareView**: Aggregated user performance profiles for sharing

**Error Handling:**

*   Centralized global exception handling for various error scenarios

**Contributing:**

*   Fork the repository and submit pull requests with clear descriptions and documentation
*   Follow standard coding conventions and best practices

**License:**

*   MIT License

This README should provide a comprehensive introduction to the CodePing-Server project, including its technical stack, key features, and operational instructions. It adheres to enterprise-grade documentation standards and UI/UX best practices for readability.
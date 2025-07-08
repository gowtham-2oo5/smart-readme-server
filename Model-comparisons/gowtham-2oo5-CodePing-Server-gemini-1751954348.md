<div align="center">
  <h1>🚀 CodePing Core Server</h1>
  <p><em>The unified backend powering competitive programming data aggregation and user management.</em></p>
  
  <!-- MAIN TECH STACK ONLY - Beautiful, consistent badges -->
  <img src="https://img.shields.io/badge/Java-007396?style=for-the-badge&logo=java&logoColor=white" alt="Java">
  <img src="https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white" alt="Spring Boot">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Maven-C71A36?style=for-the-badge&logo=apache-maven&logoColor=white" alt="Maven">
  <img src="https://img.shields.io/badge/REST_API-00599C?style=for-the-badge&logo=rest&logoColor=white" alt="REST API">
  <img src="https://img.shields.io/badge/OpenAPI-6BA539?style=for-the-badge&logo=openapi-initiative&logoColor=white" alt="OpenAPI">
  <img src="https://img.shields.io/badge/License-Unspecified-blue.svg?style=for-the-badge" alt="License">
  
  <br><br>
  
  <!-- Quick action buttons -->
  <a href="#installation">🚀 Get Started</a> •
  <a href="#features">✨ Features</a> •
  <a href="#architecture">🏗️ Architecture</a> •
  <a href="#api-endpoints">🌐 API Endpoints</a>
</div>

<hr>

## 📖 Table of Contents
<details>
  <summary>Click to expand</summary>
  <ul>
    <li><a href="#introduction">🌟 Introduction</a></li>
    <li><a href="#project-purpose">🎯 Project Purpose & Audience</a></li>
    <li><a href="#features">✨ Features</a></li>
    <li><a href="#technology-stack">🛠️ Technology Stack</a></li>
    <li><a href="#architecture">🏗️ Architecture</a>
      <ul>
        <li><a href="#project-structure">📁 Project Structure</a></li>
        <li><a href="#data-flow-and-state-management">🔄 Data Flow & State Management</a></li>
        <li><a href="#external-api-integration-strategy">🔗 External API Integration Strategy</a></li>
        <li><a href="#caching-and-rate-limiting">🚀 Caching & Rate Limiting</a></li>
      </ul>
    </li>
    <li><a href="#installation">🚀 Installation</a>
      <ul>
        <li><a href="#prerequisites">📋 Prerequisites</a></li>
        <li><a href="#getting-started">⬇️ Getting Started</a></li>
        <li><a href="#running-the-application">▶️ Running the Application</a></li>
      </ul>
    </li>
    <li><a href="#configuration">⚙️ Configuration</a></li>
    <li><a href="#api-endpoints">🌐 API Endpoints</a></li>
    <li><a href="#error-handling">❌ Error Handling</a></li>
    <li><a href="#testing">🧪 Testing</a></li>
    <li><a href="#troubleshooting">💡 Troubleshooting</a></li>
    <li><a href="#conclusion">🎉 Conclusion</a></li>
  </ul>
</details>

---

## 🌟 Introduction

The CodePing Core Server is the robust backend engine designed to aggregate and standardize competitive programming data from various platforms. It serves as a centralized hub, providing a unified API for fetching user profiles, contest histories, and recent submissions across LeetCode, CodeChef, and Codeforces. Built with Spring Boot, it prioritizes performance, scalability, and maintainability, ensuring a seamless experience for developers building applications that rely on competitive programming insights.

This server is the backbone of the CodePing platform, abstracting away the complexities of interacting with disparate external APIs and offering a consistent data model.

## 🎯 Project Purpose & Audience

**Purpose:** To streamline the access and management of competitive programming data by providing a single, coherent API layer that integrates with multiple major platforms. This eliminates the need for frontend applications or other services to directly manage platform-specific API calls, data parsing, and rate limiting.

**Target Audience:**
*   **Frontend Developers:** Building web or mobile applications that need to display competitive programming statistics, user profiles, or contest information.
*   **Data Analysts/Scientists:** Interested in consuming structured competitive programming data for research, trend analysis, or machine learning models.
*   **System Integrators:** Looking to embed competitive programming features into broader educational or recruitment platforms.
*   **Competitive Programming Enthusiasts:** Building tools or dashboards for personal use or community projects.

## ✨ Features

The CodePing Core Server delivers a comprehensive suite of features to empower competitive programming data consumption:

*   **Multi-Platform Data Aggregation:**
    *   **LeetCode:** Retrieve detailed user profiles, historical contest performance, and recent problem submissions.
    *   **CodeChef:** Access user profiles, detailed ratings graphs, and recent submissions. **Note:** This integration specifically targets a *local CodeChef microservice* at `http://localhost:8800`, indicating a specialized scraping or API proxy for CodeChef data.
    *   **Codeforces:** Fetch user information, rating history, and recent problem statuses.

*   **Centralized User Management:**
    *   **CPUsers CRUD:** Full Create, Read, Update, Delete (CRUD) operations for internal CodePing user accounts.
    *   **Firebase UID Integration:** Links internal user accounts with Firebase authentication UIDs for secure identity management.
    *   **User Profile Management:** Store and retrieve user-specific details like email, name, short bio, social links (LinkedIn, GitHub), resume, and profile pictures.
    *   **Platform Account Linking:** Associate multiple competitive programming platform handles (LeetCode, CodeChef, Codeforces) with a single CodePing user profile.

*   **Smart Caching with Redis:**
    *   **Performance Optimization:** Aggressively caches external API responses to minimize latency and reduce load on external platforms.
    *   **Configurable TTLs:** Different cache entries (e.g., user profiles, contest history, recent submissions) have tailored expiration times to ensure data freshness while maximizing cache hits.
    *   **Cache Eviction:** Provides mechanisms to manually evict cached data, useful for immediate data synchronization or troubleshooting.

*   **Robust External API Integration:**
    *   **Asynchronous & Synchronous HTTP Clients:** Utilizes both Spring's `WebClient` (reactive) for efficient non-blocking calls and `RestTemplate` (blocking) for traditional synchronous interactions, optimized for external API communication.
    *   **Centralized Data Mapping:** Dedicated mappers for each platform (`LeetCodeMapper`, `CodeChefMapper`, `CodeforcesMapper`) ensure consistent transformation of raw API responses into well-defined internal data models.
    *   **Error Handling:** Implements a global exception handler to provide consistent, descriptive error responses for issues originating from external APIs or internal processing.

*   **API Rate Limiting:**
    *   **External API Protection:** Integrates `Bucket4j` to enforce rate limits on outgoing requests to external competitive programming APIs (e.g., 100 requests per minute), preventing IP blacklisting and ensuring fair usage.

*   **Comprehensive API Documentation:**
    *   **OpenAPI 3.0 (Swagger UI):** Automatically generates interactive API documentation, allowing developers to easily explore available endpoints, request/response schemas, and even test API calls directly from a web interface.

*   **Relational Data Persistence:**
    *   **Spring Data JPA:** Leverages JPA for seamless interaction with a relational database, persisting internal user data and their linked platform accounts and performance metrics.
    *   **Entity Relationships:** Models complex relationships between users, platforms, and performance data (e.g., `CPUsers` has `OneToMany` `PlatformUser` and `PlatformUserPerformanceData`).

*   **Scheduled Tasks:**
    *   **`@EnableScheduling`:** Enables the ability to run background tasks periodically, which can be extended for automated data refreshes, cleanup, or analytics processing. (While no specific scheduled tasks are visible, the annotation implies the capability).

## 🛠️ Technology Stack

The CodePing Core Server is built on a modern, robust, and widely adopted technology stack, ensuring high performance, scalability, and developer productivity.

*   **Primary Language:** Java 17
*   **Web Framework:** Spring Boot 3.4.5
    *   `spring-boot-starter-web`: For building RESTful APIs.
    *   `spring-boot-starter-webflux`: For reactive programming and `WebClient` for efficient non-blocking HTTP calls.
    *   `spring-boot-starter-data-redis`: For Redis integration and caching.
    *   `spring-boot-starter-cache`: Spring's caching abstraction.
    *   `spring-boot-starter-test`: For unit and integration testing.
*   **Data Persistence:**
    *   Spring Data JPA: For ORM and simplified database interactions.
    *   Hibernate (default JPA provider in Spring Boot).
    *   **Database:** Configurable (e.g., PostgreSQL, MySQL, H2). *Specific database not provided in `pom.xml`, assuming external configuration.*
*   **Caching:** Redis
*   **API Documentation:** OpenAPI 3.0 (via `springdoc-openapi-starter-webmvc-ui` - inferred from `OpenApiConfig.java`)
*   **HTTP Clients:**
    *   `WebClient` (from Spring WebFlux): Reactive, non-blocking HTTP client.
    *   `RestTemplate`: Synchronous, blocking HTTP client.
*   **Rate Limiting:** Bucket4j
*   **Utility Libraries:**
    *   Lombok: Boilerplate code reduction (`@Data`, `@Builder`, `@Slf4j`, `@RequiredArgsConstructor`).
    *   Jackson: JSON processing (used by mappers and Redis serializer).
    *   Project Reactor: Reactive programming foundation (used by WebFlux).

## 🏗️ Architecture

The CodePing Core Server employs a layered architecture with clear separation of concerns, designed for modularity, scalability, and maintainability.

### 📁 Project Structure

The project follows a standard Spring Boot application structure, enhanced with dedicated packages for clarity and organization.

```
src/main/java/com/codeping/server/coreserver/
├── CoreServerApplication.java        # Main Spring Boot application entry point
├── config/                           # Application configuration (Redis, OpenAPI, HTTP clients, Rate Limiter)
│   ├── OpenApiConfig.java
│   ├── RedisConfig.java
│   ├── RestTemplateConfig.java
│   └── WebClientConfig.java
├── controllers/                      # REST API endpoints
│   ├── CPUsersController.java
│   ├── CodeChefController.java
│   ├── CodeforcesController.java
│   ├── LeetCodeController.java
│   └── MainController.java
├── dto/                              # Data Transfer Objects
│   └── CPUserDTO.java
├── exception/                        # Global exception handling
│   └── GlobalExceptionHandler.java
├── mappers/                          # Converts external API responses to internal models
│   ├── CodeChefMapper.java
│   ├── CodeforcesMapper.java
│   └── LeetCodeMapper.java
├── models/                           # JPA Entities and Plain Old Java Objects (POJOs) for data representation
│   ├── AIReview.java
│   ├── CPUsers.java
│   ├── Contest.java
│   ├── ContestHistory.java
│   ├── Platform.java
│   ├── PlatformUser.java
│   ├── PlatformUserPerformanceData.java
│   ├── ProfileShareView.java
│   ├── RatingGraph.java
│   ├── RecentSubmission.java
│   ├── Submission.java
│   ├── UserProfile.java
│   └── UserRoles.java
├── repos/                            # Spring Data JPA repositories for database interaction
│   ├── CPUsersRepository.java
│   └── PlatformUserRepository.java
└── services/                         # Business logic and external API orchestration (interfaces)
    ├── CPUsersService.java
    ├── CodeChefService.java
    ├── CodeforcesService.java
    └── LeetCodeService.java
```

### 🔄 Data Flow & State Management

1.  **Request Ingress:** HTTP requests arrive at `@RestController` endpoints defined in the `controllers` package.
2.  **Controller Layer:** Controllers receive requests, perform basic validation, and delegate to the appropriate service layer.
3.  **Service Layer:** The core business logic resides here. Services orchestrate operations:
    *   Interacting with `repos` for internal data persistence (`CPUsers`, `PlatformUser`).
    *   Making external API calls (via `WebClient` or `RestTemplate`) to competitive programming platforms.
    *   Applying caching logic (using `@Cacheable` annotations on service methods, configured in `RedisConfig`).
    *   Applying rate limiting for external calls.
4.  **Data Mapping:** After receiving raw JSON responses from external APIs, dedicated `mappers` (e.g., `LeetCodeMapper`) transform them into standardized internal `models` (e.g., `UserProfile`, `ContestHistory`).
5.  **Repository Layer:** `repos` interfaces (Spring Data JPA) handle interactions with the relational database for `CPUsers` and `PlatformUser` entities.
6.  **Response Egress:** Processed data (often in DTOs) is returned through the service and controller layers back to the client as JSON.
7.  **State Management:**
    *   **Database:** Primary persistent state is managed in the relational database via JPA.
    *   **Redis Cache:** Acts as a secondary, volatile state store, holding frequently accessed external API data to improve response times and reduce external API calls. Cache entries have specific Time-To-Live (TTL) durations.

### 🔗 External API Integration Strategy

The server integrates with external competitive programming platforms using a dual-client approach and robust data transformation:

*   **`WebClient` for LeetCode & Codeforces:** For highly available and non-blocking interactions, `WebClient` is preferred. This allows for efficient handling of concurrent requests without blocking server threads. LeetCode uses a GraphQL endpoint, while Codeforces uses a standard REST API.
*   **`RestTemplate` for Rate Limited Calls:** While `WebClient` is generally preferred, `RestTemplate` is configured with `Bucket4j` for explicit rate limiting. This ensures that the server respects external API rate limits, preventing IP bans or service degradation.
*   **Local CodeChef Microservice:** A unique aspect is the dependency on a local microservice for CodeChef data (`http://localhost:8800`). This implies that direct interaction with CodeChef's public API is handled by a separate application, likely due to complex scraping requirements or specific API access patterns. **This microservice must be running alongside CodePing Core Server for CodeChef features to work.**
*   **Dedicated Mappers:** Each platform has a dedicated mapper component responsible for parsing the platform's unique JSON response structure into the common `CodePing` models (`UserProfile`, `ContestHistory`, `Submission`). This centralizes parsing logic and isolates changes if an external API's response format evolves.

### 🚀 Caching & Rate Limiting

*   **Caching:** Redis is integrated via `spring-boot-starter-data-redis` and `spring-boot-starter-cache`. `RedisConfig` defines a `RedisCacheManager` with a default TTL of 7 days, but also custom TTLs for specific caches like `userProfiles` (1 day), `contestHistory` (1 hour), and `recentSubmissions` (15 minutes). This granular control optimizes data freshness for different data types.
*   **Rate Limiting:** `RestTemplateConfig` sets up a `Bucket` from `Bucket4j` that limits requests to 100 per minute. This bucket should be integrated with `RestTemplate` calls to external APIs to prevent overwhelming them.

## 🚀 Installation

Follow these steps to set up and run the CodePing Core Server on your local machine.

### 📋 Prerequisites

Before you begin, ensure you have the following installed:

*   **Java Development Kit (JDK):** Version 17 or higher.
    *   Verify with: `java -version`
*   **Maven:** Version 3.6.3 or higher.
    *   Verify with: `mvn --version`
*   **Git:** For cloning the repository.
    *   Verify with: `git --version`
*   **Docker (Recommended for Redis):** For easily running a Redis instance.
    *   Verify with: `docker --version`
*   **CodeChef Local Microservice:** As identified in the `WebClientConfig` and `CodeChefService`, a separate service that exposes CodeChef data at `http://localhost:8800` is required for CodeChef integration to function. Ensure this service is running and accessible. Instructions for setting up this service are outside the scope of this README.

### ⬇️ Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/gowtham-2oo5/CodePing-Server.git
    cd CodePing-Server
    ```

2.  **Start Redis (using Docker):**
    If you don't have Redis running, the simplest way is via Docker:
    ```bash
    docker run -d --name code-ping-redis -p 6379:6379 redis/redis-stack-server:latest
    ```
    This command starts a Redis server and exposes it on port `6379`.

3.  **Build the project:**
    Compile the Java source code and package it into a JAR file.
    ```bash
    mvn clean install
    ```
    This command will download all necessary dependencies and build the project.

### ▶️ Running the Application

After building, you can run the Spring Boot application:

```bash
java -jar target/Core-Server-0.0.1-SNAPSHOT.jar
```

Alternatively, if you are using an IDE like IntelliJ IDEA or VS Code:
1.  Open the project in your IDE.
2.  Locate `src/main/java/com/codeping/server/coreserver/CoreServerApplication.java`.
3.  Run the `main` method from your IDE.

Upon successful startup, you should see output similar to:
```
Working, http://localhost:8080/
```
The server will be running on `http://localhost:8080`.

## ⚙️ Configuration

The server's behavior can be configured via `application.properties` (or `application.yml` if preferred) in `src/main/resources`. Key configurations include:

*   **Server Port:**
    ```properties
    server.port=8080
    ```
*   **Redis Connection:**
    ```properties
    spring.data.redis.host=localhost
    spring.data.redis.port=6379
    ```
    *Ensure your Redis instance is running at these host and port.*
*   **Database (JPA):**
    While no specific database is configured in `pom.xml`, Spring Boot automatically configures an in-memory H2 database by default if no other database dependencies are provided. For a production environment, you would configure an external relational database (e.g., PostgreSQL, MySQL).
    Example for PostgreSQL:
    ```properties
    spring.datasource.url=jdbc:postgresql://localhost:5432/codeping_db
    spring.datasource.username=codeping_user
    spring.datasource.password=your_password
    spring.jpa.hibernate.ddl-auto=update # or create, create-drop, none
    spring.jpa.show-sql=true
    ```
*   **CodeChef Microservice URL:**
    The `CodeChefService` interface hardcodes `http://localhost:8800`. For production or different deployment scenarios, this should ideally be externalized to `application.properties` using a `@Value` annotation in the service implementation.
    ```properties
    # Not currently configurable via properties, hardcoded in interface.
    # Future enhancement: externalize this URL.
    # codeping.codechef.base-url=http://your-codechef-microservice:8800
    ```
*   **Logging:**
    ```properties
    logging.level.com.codeping.server=INFO
    ```
    Adjust logging levels for more or less verbosity.

## 🌐 API Endpoints

The CodePing Core Server exposes RESTful APIs for managing users and fetching competitive programming data.

All API endpoints are documented interactively via **Swagger UI**, accessible at:
[http://localhost:8080/swagger-ui.html](http://localhost:8080/swagger-ui.html)

Here's a summary of the main endpoint categories:

### 👤 User Management (`/api/v1/users`)
Managed by `CPUsersController`.
*   `POST /api/v1/users`: Create a new CodePing user.
*   `PUT /api/v1/users/{id}`: Update an existing user by ID.
*   `DELETE /api/v1/users/{id}`: Delete a user by ID.
*   `GET /api/v1/users/{id}`: Retrieve a user by ID.
*   `GET /api/v1/users/email/{email}`: Retrieve a user by email address.
*   `GET /api/v1/users/firebaseUid/{firebaseUid}`: Retrieve a user by Firebase UID.
*   `GET /api/v1/users`: Get all registered users.

### 👨‍💻 CodeChef Integration (`/api/codechef`)
Managed by `CodeChefController`.
*   `GET /api/codechef/profile/{username}`: Get user profile.
*   `GET /api/codechef/ratings/{username}`: Get ratings graph.
*   `GET /api/codechef/recent-submissions/{username}`: Get recent submissions.
*   `GET /api/codechef/upcoming-contests`: Get upcoming contests.

### 🖥️ Codeforces Integration (`/api/codeforces`)
Managed by `CodeforcesController`.
*   `GET /api/codeforces/profile/{handle}`: Get user profile.
*   `GET /api/codeforces/rating/{handle}`: Get user rating history.
*   `GET /api/codeforces/recent-submissions/{handle}`: Get recent submissions.
*   `GET /api/codeforces/upcoming-contests`: Get upcoming contests.

### 💡 LeetCode Integration (`/api/leetcode`)
Managed by `LeetCodeController`.
*   `GET /api/leetcode/profile/{username}`: Get user profile.
*   `GET /api/leetcode/contest-history/{username}`: Get contest history.
*   `GET /api/leetcode/recent-submissions/{username}`: Get recent submissions.
*   `GET /api/leetcode/upcoming-contests`: Get upcoming contests.

### 🏠 Root API (`/api`)
Managed by `MainController`.
*   `GET /api`: Simple health check, returns "Hello World".

## ❌ Error Handling

The server implements a `GlobalExceptionHandler` to provide consistent and informative error responses. Common error types handled include:

*   **`EntityNotFoundException` (HTTP 404 Not Found):** For resources not found in the database.
*   **`HttpClientErrorException` (Dynamic HTTP Status):** For errors encountered when calling external APIs (e.g., 404 from LeetCode, 429 from Codeforces due to rate limits). The original HTTP status from the external service is propagated.
*   **`RuntimeException` (HTTP 500 Internal Server Error):** A catch-all for unexpected internal server errors.

Each error response includes a `timestamp`, `status`, `error` type, and a `message`.

## 🧪 Testing

The project includes unit and integration tests using Spring Boot's testing capabilities.

*   `spring-boot-starter-test`: Provides JUnit 5, Mockito, AssertJ, and Spring Test.
*   `reactor-test`: For testing reactive components (e.g., `WebClient` interactions).

To run the tests:

```bash
mvn test
```
This command executes all tests found in the `src/test/java` directory. While no specific test files were provided in the analysis, the presence of test dependencies indicates a commitment to testability.

## 💡 Troubleshooting

Here are some common issues and their potential solutions:

*   **"Connection refused: Redis"**:
    *   **Cause:** Redis server is not running or is not accessible on the configured host/port.
    *   **Solution:** Ensure your Redis instance is running (e.g., `docker ps` to check your Docker container) and that `spring.data.redis.host` and `spring.data.redis.port` in `application.properties` are correct.
*   **CodeChef integration issues (e.g., 404, 500 from CodeChef endpoints)**:
    *   **Cause:** The CodeChef local microservice (expected at `http://localhost:8800`) is not running or is inaccessible.
    *   **Solution:** Verify that the CodeChef microservice is running and listening on port `8800`.
*   **"Rate limit exceeded" (HTTP 429) errors from LeetCode/Codeforces**:
    *   **Cause:** The server has made too many requests to an external API within a short period, even with `Bucket4j` rate limiting. This can happen if the `Bucket4j` configuration needs adjustment or if multiple instances are hitting the same external IP.
    *   **Solution:** Reduce the frequency of your API calls. If you are developing, consider using cached data or increasing the `Bucket4j` limits (for testing purposes only, respect public API terms of service).
*   **`EntityNotFoundException` for user operations**:
    *   **Cause:** Attempting to retrieve, update, or delete a user with an ID or email that does not exist in the database.
    *   **Solution:** Double-check the ID or email provided in your request.
*   **Build failures (`mvn clean install`)**:
    *   **Cause:** Missing Maven dependencies, Java version mismatch, or compilation errors.
    *   **Solution:** Ensure you have JDK 17 installed and configured correctly. Check Maven output for specific error messages. Run `mvn dependency:resolve` to diagnose dependency issues.

---

## 🎉 Conclusion

The CodePing Core Server stands as a critical component for anyone looking to build applications around competitive programming data. With its strong foundation in Java and Spring Boot, coupled with intelligent caching, robust external API integrations, and comprehensive user management, it offers a streamlined and scalable solution for accessing unified performance metrics from major competitive programming platforms.

### 🌟 What's Next?
The architecture is primed for expansion. Future enhancements could include:
*   [ ] Integration with more competitive programming platforms.
*   [ ] Implementation of the `AIReview` model, potentially leveraging the `spring-ai` dependency for code analysis or personalized feedback.
*   [ ] Advanced analytics and visualization features.
*   [ ] Webhook support for real-time data updates.
*   [ ] More sophisticated error handling and monitoring.

### 🤝 Contributing
We welcome contributions to make CodePing Core Server even better! Please:
1.  Fork the repository.
2.  Create a feature branch for your changes (`git checkout -b feature/your-feature-name`).
3.  Make your modifications and ensure tests pass.
4.  Commit your changes (`git commit -m 'Feat: Add new feature'`).
5.  Push to your branch (`git push origin feature/your-feature-name`).
6.  Submit a pull request.

### 📞 Support & Contact
*   🐛 Issues: Please report any bugs or feature requests via GitHub Issues.
*   💬 Questions: Feel free to open a discussion on the repository if you have general questions or need guidance.

---

<div align="center">
  <strong>⭐ Star this repo if you find it helpful!</strong>
  <br>
  <em>Made with ❤️ for the developer community</em>
</div>
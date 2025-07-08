<div align="center">
  <h1>🚀 CodePing-Server</h1>
  <p><em>The robust backend service powering unified competitive programming insights.</em></p>

  <!-- MAIN TECH STACK ONLY - Beautiful, consistent badges -->
  <img src="https://img.shields.io/badge/Java-007396?style=for-the-badge&logo=openjdk&logoColor=white" alt="Java">
  <img src="https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white" alt="Spring Boot">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Maven-C71A36?style=for-the-badge&logo=apache-maven&logoColor=white" alt="Maven">
  <img src="https://img.shields.io/badge/OpenAPI-6BA54F?style=for-the-badge&logo=openapi-initiative&logoColor=white" alt="OpenAPI">
  <img src="https://img.shields.io/badge/License-Unspecified-lightgrey.svg?style=for-the-badge" alt="License">

  <br><br>

  <!-- Quick action buttons -->
  <a href="#installation">🚀 Get Started</a> •
  <a href="#features">✨ Features</a> •
  <a href="#api-endpoints">🔗 API Endpoints</a> •
  <a href="#contributing">🤝 Contributing</a>
</div>

<hr>

## 📖 Table of Contents
<details>
  <summary>Click to expand</summary>
  <ol>
    <li><a href="#overview">Overview</a></li>
    <li><a href="#features">Features</a></li>
    <li><a href="#architecture">Architecture</a></li>
    <li><a href="#technology-stack">Technology Stack</a></li>
    <li><a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#running-the-application">Running the Application</a></li>
      </ul>
    </li>
    <li><a href="#api-endpoints">API Endpoints</a>
      <ul>
        <li><a href="#user-management">User Management</a></li>
        <li><a href="#codechef-integration">CodeChef Integration</a></li>
        <li><a href="#codeforces-integration">Codeforces Integration</a></li>
        <li><a href="#leetcode-integration">LeetCode Integration</a></li>
        <li><a href="#api-documentation">API Documentation (Swagger UI)</a></li>
      </ul>
    </li>
    <li><a href="#configuration">Configuration</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#conclusion">Conclusion</a></li>
  </ol>
</details>

---

## 💡 Overview

CodePing-Server is the core backend service for the CodePing platform, designed to aggregate and unify data from various competitive programming platforms like LeetCode, CodeChef, and Codeforces. It acts as an intelligent proxy, providing a consistent API for user profiles, contest histories, and recent submissions, while implementing critical features like caching and rate limiting.

This server is built with Spring Boot, ensuring a robust, scalable, and maintainable foundation for enterprise-grade applications. Its modular design allows for easy integration with front-end applications and other microservices.

**Target Audience:** This repository is primarily for developers looking to understand, extend, or contribute to the CodePing backend. It's also valuable for anyone building applications that require consolidated competitive programming data.

---

## ✨ Features

CodePing-Server offers a rich set of features meticulously engineered for performance and reliability:

*   **Unified Data Aggregation:**
    *   **LeetCode Integration:** Seamlessly retrieves user profiles, contest histories, and recent submissions directly from LeetCode's GraphQL API.
    *   **CodeChef Integration:** Integrates with a local CodeChef microservice (expected at `http://localhost:8800`) to fetch user profiles, rating graphs, recent submissions, and upcoming contest data.
    *   **Codeforces Integration:** Connects to the public Codeforces API to gather user information, rating history, recent submissions, and contest lists.

*   **Comprehensive User Data APIs:**
    *   **User Profiles:** Provides consolidated profile information (username, real name, ratings, ranks) across integrated platforms.
    *   **Contest History:** Fetches and normalizes contest participation details, including ratings changes and ranks.
    *   **Recent Submissions:** Retrieves a user's latest accepted submissions, linking directly to problem statements.

*   **Internal User Management:**
    *   **CRUD Operations:** Full Create, Read, Update, Delete capabilities for internal CodePing user accounts (`CPUsers`), enabling robust user management.
    *   **Firebase UID Integration:** Supports integration with Firebase for external authentication, linking internal user profiles to Firebase UIDs.

*   **Smart Caching with Redis:**
    *   **Optimized Performance:** Leverages Spring Cache Abstraction with Redis to cache frequently accessed data (user profiles, contest history, recent submissions).
    *   **Granular TTLs:** Configured with specific Time-To-Live (TTL) durations for different data types to ensure data freshness while maximizing performance (e.g., user profiles cached for 1 day, recent submissions for 15 minutes).

*   **Robust External API Handling:**
    *   **Reactive and Synchronous Clients:** Utilizes both Spring WebFlux's `WebClient` for reactive, non-blocking calls (LeetCode, Codeforces) and `RestTemplate` for synchronous interactions (CodeChef microservice).
    *   **Configurable Timeouts:** HTTP clients are configured with appropriate connection and read timeouts to prevent resource exhaustion.
    *   **Rate Limiting:** Implements `Bucket4j` for intelligent rate limiting on outgoing requests (100 requests per minute) to external APIs, preventing abuse and ensuring fair usage.

*   **Centralized Error Handling:**
    *   **Global Exception Handling:** Provides a unified and consistent error response structure across the API for common exceptions like `EntityNotFoundException` and `HttpClientErrorException`.
    *   **Informative Error Messages:** Error responses include timestamp, HTTP status, error type, and a descriptive message for easier debugging.

*   **Comprehensive API Documentation:**
    *   **OpenAPI (Swagger UI):** Automatically generates and serves interactive API documentation, making it easy for developers to explore available endpoints, request/response schemas, and try out API calls.

---

## 🏗️ Architecture

CodePing-Server is designed with a layered, modular architecture based on the principles of **Domain-Driven Design** and **RESTful API design**.

<details>
  <summary><strong>📁 Project Structure Breakdown</strong></summary>

  ```
  CodePing-Server/
  ├── src/
  │   ├── main/
  │   │   ├── java/
  │   │   │   └── com/codeping/server/coreserver/
  │   │   │       ├── CoreServerApplication.java  # Main Spring Boot entry point
  │   │   │       ├── config/                   # Spring configuration classes
  │   │   │       │   ├── OpenApiConfig.java    # Swagger/OpenAPI documentation setup
  │   │   │       │   ├── RedisConfig.java      # Redis caching configuration
  │   │   │       │   ├── RestTemplateConfig.java # Synchronous HTTP client & rate limiting
  │   │   │       │   └── WebClientConfig.java  # Reactive HTTP clients for external APIs
  │   │   │       ├── controllers/              # REST API controllers (entry points)
  │   │   │       │   ├── CPUsersController.java # Internal user management API
  │   │   │       │   ├── CodeChefController.java # CodeChef data API
  │   │   │       │   ├── CodeforcesController.java # Codeforces data API
  │   │   │       │   ├── LeetCodeController.java # LeetCode data API
  │   │   │       │   └── MainController.java   # Basic health check endpoint
  │   │   │       ├── dto/                      # Data Transfer Objects
  │   │   │       │   └── CPUserDTO.java        # DTO for internal users
  │   │   │       ├── exception/                # Global exception handling
  │   │   │       │   └── GlobalExceptionHandler.java
  │   │   │       ├── mappers/                  # Mappers for transforming external API responses
  │   │   │       │   ├── CodeChefMapper.java
  │   │   │       │   ├── CodeforcesMapper.java
  │   │   │       │   └── LeetCodeMapper.java
  │   │   │       ├── models/                   # JPA Entities & domain models
  │   │   │       │   ├── AIReview.java
  │   │   │       │   ├── CPUsers.java
  │   │   │       │   ├── Contest.java
  │   │   │       │   ├── ContestHistory.java
  │   │   │       │   ├── Platform.java
  │   │   │       │   ├── PlatformUser.java
  │   │   │       │   ├── PlatformUserPerformanceData.java
  │   │   │       │   ├── ProfileShareView.java
  │   │   │       │   ├── RatingGraph.java
  │   │   │       │   ├── RecentSubmission.java
  │   │   │       │   ├── Submission.java
  │   │   │       │   ├── UserProfile.java
  │   │   │       │   └── UserRoles.java
  │   │   │       ├── repos/                    # Spring Data JPA repositories
  │   │   │       │   ├── CPUsersRepository.java
  │   │   │       │   └── PlatformUserRepository.java
  │   │   │       └── services/                 # Business logic interfaces
  │   │   │           ├── CPUsersService.java
  │   │   │           ├── CodeChefService.java
  │   │   │           ├── CodeforcesService.java
  │   │   │           └── LeetCodeService.java
  │   │   └── resources/
  │   │       └── application.properties        # Application properties/configuration (not provided, but implied)
  │   └── test/                                 # Unit and integration tests
  └── pom.xml                                 # Maven Project Object Model
  ```
</details>

### Architectural Patterns

*   **Layered Architecture:** The application strictly adheres to a layered architecture:
    *   **Presentation Layer (Controllers):** Handles incoming HTTP requests, performs input validation, and orchestrates calls to the service layer.
    *   **Service Layer (Services):** Encapsulates the core business logic, orchestrates data retrieval from external APIs, applies caching, and interacts with repositories. This layer defines abstract interfaces (e.g., `CPUsersService`, `CodeChefService`).
    *   **Data Access Layer (Repositories):** Manages persistence operations with the database using Spring Data JPA.
    *   **Domain Layer (Models/DTOs):** Contains the core business entities, value objects, and data transfer objects.

*   **RESTful API Design:** All external-facing APIs are designed following REST principles, using standard HTTP methods (GET, POST, PUT, DELETE) and resource-oriented URLs.

*   **Dependency Injection (DI):** Spring's powerful DI container is extensively used to manage component lifecycles and inject dependencies, promoting loose coupling and testability.

*   **Caching Strategy:** Spring's Caching Abstraction is employed, backed by Redis, to significantly reduce latency and load on external APIs by storing frequently accessed data. Cache configurations are granular, with distinct TTLs for different data types.

*   **External Service Integration:** The service layer abstracts the complexities of integrating with external competitive programming platforms. `WebClient` is used for reactive, non-blocking calls (e.g., LeetCode, Codeforces), while `RestTemplate` handles synchronous communication with the local CodeChef microservice.

*   **Global Exception Handling:** A dedicated global exception handler ensures that all API errors are caught, logged, and returned with consistent, informative error responses, improving API usability and debugging.

---

## 🛠️ Technology Stack

This project is built on a robust set of modern enterprise technologies:

*   **Core Language:** <img src="https://img.shields.io/badge/Java-007396?style=for-the-badge&logo=openjdk&logoColor=white" alt="Java"> (Version 17)
*   **Backend Framework:** <img src="https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white" alt="Spring Boot"> (Version 3.4.5)
    *   **Spring Web:** For building RESTful APIs.
    *   **Spring WebFlux & Project Reactor:** For reactive programming and non-blocking I/O, especially for external API calls.
    *   **Spring Data JPA:** For simplified data access and persistence with relational databases.
    *   **Spring Data Redis:** For integrating with Redis as a caching layer.
    *   **Spring Boot Starter Cache:** Spring's caching abstraction.
    *   **Lombok:** To reduce boilerplate code (getters, setters, constructors).
*   **Caching:** <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
*   **Build Tool:** <img src="https://img.shields.io/badge/Maven-C71A36?style=for-the-badge&logo=apache-maven&logoColor=white" alt="Maven">
*   **API Documentation:** <img src="https://img.shields.io/badge/OpenAPI-6BA54F?style=for-the-badge&logo=openapi-initiative&logoColor=white" alt="OpenAPI"> (Swagger UI)
*   **HTTP Clients:**
    *   `org.springframework.web.client.RestTemplate`
    *   `org.springframework.web.reactive.function.client.WebClient`
*   **Rate Limiting:** `io.github.bucket4j.Bucket`
*   **JSON Processing:** `com.fasterxml.jackson.databind.ObjectMapper`
*   **Database:** A relational database (e.g., PostgreSQL, MySQL, H2) is required for JPA. Specific driver is not in `pom.xml` snippet but is a standard Spring Data JPA dependency.

---

## 🚀 Getting Started

Follow these steps to get CodePing-Server up and running on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:

*   **Java Development Kit (JDK):** Version 17 or higher.
    *   [Download JDK 17](https://www.oracle.com/java/technologies/downloads/)
*   **Apache Maven:** Version 3.6 or higher.
    *   [Download Maven](https://maven.apache.org/download.cgi)
*   **Git:** For cloning the repository.
    *   [Download Git](https://git-scm.com/downloads)
*   **Redis Server:** A running instance of Redis.
    *   [Install Redis](https://redis.io/docs/getting-started/installation/) (e.g., using Docker: `docker run --name my-redis -p 6379:6379 -d redis/redis-stack-server`)
*   **Relational Database:** A database like PostgreSQL or MySQL. Ensure you have a database schema ready for Spring Data JPA to connect to. You'll need to configure connection details in `application.properties`.
    *   **Note:** The provided source implies a relational database but doesn't include the JDBC driver in the `pom.xml` snippet. You'll need to add a dependency for your chosen database (e.g., `spring-boot-starter-data-jpa` usually includes H2 by default, but for production, you'd add `mysql-connector-j` or `postgresql`).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/gowtham-2oo5/CodePing-Server.git
    cd CodePing-Server
    ```

2.  **Build the project with Maven:**
    This command will download all necessary dependencies and compile the project.
    ```bash
    mvn clean install
    ```

3.  **Configure `application.properties`:**
    Create `src/main/resources/application.properties` (if it doesn't exist) and configure your database and Redis connection details.

    Example `src/main/resources/application.properties`:
    ```properties
    # Server Port
    server.port=8080

    # Redis Configuration
    spring.data.redis.host=localhost
    spring.data.redis.port=6379
    spring.data.redis.password= # Your Redis password if any

    # Database Configuration (Example for PostgreSQL)
    spring.datasource.url=jdbc:postgresql://localhost:5432/codeping_db
    spring.datasource.username=codeping_user
    spring.datasource.password=your_db_password
    spring.datasource.driver-class-name=org.postgresql.Driver

    # JPA and Hibernate Properties
    spring.jpa.hibernate.ddl-auto=update # Use 'create' or 'create-drop' for initial setup, 'update' for migrations
    spring.jpa.show-sql=true
    spring.jpa.properties.hibernate.format_sql=true
    spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect

    # Spring Cache configuration (optional, can be done programmatically in RedisConfig)
    spring.cache.type=redis

    # CodeChef Microservice URL (if running locally)
    # Ensure your CodeChef scraper microservice is running at this address
    # If not running, CodeChef endpoints will throw errors
    # codechef.base.url=http://localhost:8800
    ```

    **Important:** The `CodeChefService` is configured to connect to a local microservice at `http://localhost:8800`. If you intend to use CodeChef integration, ensure this microservice is running and accessible.

### Running the Application

After building and configuring, you can run the Spring Boot application:

```bash
mvn spring-boot:run
```

The application should start on `http://localhost:8080/`. You will see "Working, http://localhost:8080/" printed in the console if successful.

---

## 🔗 API Endpoints

CodePing-Server exposes a comprehensive set of RESTful APIs. You can explore these APIs interactively via Swagger UI once the server is running.

### User Management (`/api/v1/users`)

This API manages internal CodePing user profiles.

*   **`POST /api/v1/users`**
    *   **Description:** Creates a new user.
    *   **Request Body:** `CPUserDTO` (email, name, firebaseUid, etc.)
    *   **Responses:** `201 Created`, `400 Bad Request`, `409 Conflict` (user already exists)

*   **`PUT /api/v1/users/{id}`**
    *   **Description:** Updates an existing user by ID.
    *   **Path Variable:** `id` (UUID of the user)
    *   **Request Body:** `CPUserDTO` (updated user details)
    *   **Responses:** `200 OK`, `400 Bad Request`, `404 Not Found`

*   **`DELETE /api/v1/users/{id}`**
    *   **Description:** Deletes a user by ID.
    *   **Path Variable:** `id` (UUID of the user)
    *   **Responses:** `204 No Content`, `404 Not Found`

*   **`GET /api/v1/users/{id}`**
    *   **Description:** Retrieves a user by ID.
    *   **Path Variable:** `id` (UUID of the user)
    *   **Responses:** `200 OK`, `404 Not Found`

*   **`GET /api/v1/users/email/{email}`**
    *   **Description:** Retrieves a user by email address.
    *   **Path Variable:** `email` (User's email)
    *   **Responses:** `200 OK`, `404 Not Found`

*   **`GET /api/v1/users/firebase/{firebaseUid}`**
    *   **Description:** Retrieves a user by Firebase UID.
    *   **Path Variable:** `firebaseUid` (User's Firebase UID)
    *   **Responses:** `200 OK`, `404 Not Found`

*   **`GET /api/v1/users`**
    *   **Description:** Retrieves all users.
    *   **Responses:** `200 OK`

### CodeChef Integration (`/api/codechef`)

APIs for fetching data from the CodeChef platform.

*   **`GET /api/codechef/profile/{username}`**
    *   **Description:** Retrieves a user's CodeChef profile.
    *   **Path Variable:** `username` (CodeChef handle)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/codechef/ratings/{username}`**
    *   **Description:** Retrieves a user's CodeChef ratings graph history.
    *   **Path Variable:** `username` (CodeChef handle)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/codechef/recent-submissions/{username}`**
    *   **Description:** Retrieves a user's recent CodeChef submissions.
    *   **Path Variable:** `username` (CodeChef handle)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/codechef/upcoming-contests`**
    *   **Description:** Retrieves upcoming CodeChef contests.
    *   **Responses:** `200 OK`, `429 Too Many Requests`

### Codeforces Integration (`/api/codeforces`)

APIs for fetching data from the Codeforces platform.

*   **`GET /api/codeforces/profile/{handle}`**
    *   **Description:** Retrieves a user's Codeforces profile.
    *   **Path Variable:** `handle` (Codeforces handle)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/codeforces/rating/{handle}`**
    *   **Description:** Retrieves a user's Codeforces rating history.
    *   **Path Variable:** `handle` (Codeforces handle)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/codeforces/recent-submissions/{handle}`**
    *   **Description:** Retrieves a user's recent Codeforces submissions.
    *   **Path Variable:** `handle` (Codeforces handle)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/codeforces/upcoming-contests`**
    *   **Description:** Retrieves upcoming Codeforces contests.
    *   **Responses:** `200 OK`, `429 Too Many Requests`

### LeetCode Integration (`/api/leetcode`)

APIs for fetching data from the LeetCode platform.

*   **`GET /api/leetcode/profile/{username}`**
    *   **Description:** Retrieves a user's LeetCode profile.
    *   **Path Variable:** `username` (LeetCode username)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/leetcode/contest-history/{username}`**
    *   **Description:** Retrieves a user's LeetCode contest history.
    *   **Path Variable:** `username` (LeetCode username)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/leetcode/recent-submissions/{username}`**
    *   **Description:** Retrieves a user's recent LeetCode submissions.
    *   **Path Variable:** `username` (LeetCode username)
    *   **Responses:** `200 OK`, `404 Not Found`, `429 Too Many Requests`

*   **`GET /api/leetcode/upcoming-contests`**
    *   **Description:** Retrieves upcoming LeetCode contests.
    *   **Responses:** `200 OK`, `429 Too Many Requests`

### API Documentation (Swagger UI)

Once the server is running, you can access the interactive API documentation at:
`http://localhost:8080/swagger-ui.html`

This interface allows you to view all available endpoints, their parameters, and response structures, and even make test calls directly from your browser.

---

## ⚙️ Configuration

Key configurations are managed via `src/main/resources/application.properties`.

*   **Server Port:**
    ```properties
    server.port=8080
    ```
*   **Redis:**
    ```properties
    spring.data.redis.host=localhost
    spring.data.redis.port=6379
    spring.data.redis.password=
    ```
*   **Database:** (Example for PostgreSQL)
    ```properties
    spring.datasource.url=jdbc:postgresql://localhost:5432/codeping_db
    spring.datasource.username=codeping_user
    spring.datasource.password=your_db_password
    spring.datasource.driver-class-name=org.postgresql.Driver
    spring.jpa.hibernate.ddl-auto=update # Important: Choose carefully for production
    ```
*   **External Service Base URLs:** These are hardcoded as constants within the `services` interfaces. For production deployment, it's recommended to externalize these into `application.properties` for easier management.
    *   **CodeChef:** `http://localhost:8800` (configurable via `codechef.base.url` if added)
    *   **Codeforces:** `https://codeforces.com/api`
    *   **LeetCode:** `https://leetcode.com/graphql`

---

## 🐛 Troubleshooting

*   **"Address already in use: bind"**:
    *   **Issue:** The server port (default 8080) is already occupied by another application.
    *   **Solution:** Change `server.port` in `application.properties` to a different value (e.g., 8081) or stop the conflicting application.

*   **"Failed to connect to Redis" / "Connection refused"**:
    *   **Issue:** Redis server is not running or is inaccessible at the configured host/port.
    *   **Solution:**
        1.  Ensure Redis is running (e.g., `redis-server` or `docker ps` if using Docker).
        2.  Verify `spring.data.redis.host` and `spring.data.redis.port` in `application.properties` are correct.
        3.  Check firewall settings if Redis is on a different machine.

*   **"Cannot connect to database" / "No suitable driver"**:
    *   **Issue:** Database is not running, connection details are incorrect, or the JDBC driver is missing.
    *   **Solution:**
        1.  Ensure your database (PostgreSQL, MySQL, etc.) is running.
        2.  Double-check `spring.datasource.url`, `username`, `password` in `application.properties`.
        3.  Make sure you have the correct JDBC driver dependency in your `pom.xml`. For PostgreSQL, add:
            ```xml
            <dependency>
                <groupId>org.postgresql</groupId>
                <artifactId>postgresql</artifactId>
                <scope>runtime</scope>
            </dependency>
            ```
        4.  Ensure `spring.jpa.hibernate.ddl-auto` is set appropriately for your initial setup (e.g., `create` or `create-drop` for first run, then `update`).

*   **"Error mapping ... response" / "RuntimeException" from Mappers**:
    *   **Issue:** The external API response structure has changed or is unexpected, causing mapping failures.
    *   **Solution:** Check the logs for the exact error message. Verify the external API's current response format against the mappers (`CodeChefMapper`, `CodeforcesMapper`, `LeetCodeMapper`). Update the mappers if the external API contract has changed.

*   **`429 Too Many Requests` from external APIs**:
    *   **Issue:** The built-in rate limiter (100 req/min) might be too aggressive for certain external APIs, or you're making too many requests quickly.
    *   **Solution:** Reduce your request rate or adjust the rate limiter configuration in `RestTemplateConfig.java`. Be mindful of external API policies.

---

## 🤝 Contributing

We welcome contributions to CodePing-Server! Your efforts help improve the platform for everyone.

To contribute:
1.  **Fork the repository:** Click the "Fork" button at the top right of this page.
2.  **Clone your forked repository:**
    ```bash
    git clone https://github.com/YOUR_GITHUB_USERNAME/CodePing-Server.git
    cd CodePing-Server
    ```
3.  **Create a new branch:** Choose a descriptive name for your branch (e.g., `feature/add-new-platform`, `fix/bug-in-cache`).
    ```bash
    git checkout -b feature/your-feature-name
    ```
4.  **Make your changes:** Implement your features or bug fixes.
5.  **Write tests:** Ensure your changes are covered by appropriate unit or integration tests.
6.  **Commit your changes:** Write clear and concise commit messages.
    ```bash
    git commit -m "feat: Add new feature or fix bug"
    ```
7.  **Push to your forked repository:**
    ```bash
    git push origin feature/your-feature-name
    ```
8.  **Create a Pull Request (PR):** Go to the original CodePing-Server repository on GitHub and create a new pull request from your forked branch. Provide a detailed description of your changes.

---

## 🎉 Conclusion

CodePing-Server stands as a testament to modern backend engineering, seamlessly integrating disparate competitive programming platforms into a unified, high-performance API. Built with Spring Boot and leveraging powerful features like Redis caching, reactive programming with WebFlux, and robust error handling, it provides a solid foundation for any application requiring consolidated developer performance insights.

### 🌟 What's Next?
*   [ ] Enhance AI Review functionality (Spring AI dependency exists, indicating future plans).
*   [ ] Introduce more competitive programming platforms.
*   [ ] Implement advanced analytics and insights.
*   [ ] Explore distributed tracing and monitoring for microservices.

### 📞 Support & Contact
*   🐛 **Issues:** If you find a bug or have a feature request, please open an issue on GitHub.
*   💬 **Questions:** For general inquiries or discussions, feel free to open a discussion on the repository.

---

<div align="center">
  <strong>⭐ Star this repo if you find it helpful!</strong>
  <br>
  <em>Made with ❤️ for the developer community</em>
</div>
<div align="center">
  <h1>🚀 CodePing-Server</h1>
  <p><em>Unifying competitive programming data to empower developers and enhance their skills.</em></p>

  <img src="https://img.shields.io/badge/Java-ED8B59?style=for-the-badge&logo=java&logoColor=white" alt="Java">
  <img src="https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=spring&logoColor=white" alt="Spring Boot">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=white" alt="Swagger">
  <img src="https://img.shields.io/badge/Lombok-FF7777?style=for-the-badge&logo=lombok" alt="Lombok">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License">

  <br><br>

  <a href="#introduction">📖 Introduction</a> •
  <a href="#features">✨ Features</a> •
  <a href="#architecture">🏛️ Architecture</a> •
  <a href="#installation">⚙️ Installation</a> •
  <a href="#api-endpoints">🔗 API Endpoints</a> •
  <a href="#configuration">🛠️ Configuration</a> •
  <a href="#testing">✅ Testing</a> •
  <a href="#troubleshooting">❓ Troubleshooting</a> •
  <a href="#contributing">🤝 Contributing</a>
</div>

<hr>

## 📖 Introduction

CodePing-Server is a backend service designed to aggregate and provide a unified interface for data from various competitive programming platforms such as LeetCode, CodeChef, and Codeforces. It offers features like user profile retrieval, contest history, recent submissions tracking, and more. The server is built using Spring Boot and leverages Redis for caching to improve performance and reduce API request latency. It employs RESTful APIs for seamless integration with front-end applications.

The primary purpose is to create a centralized hub for competitive programming data, enabling developers to track their progress across multiple platforms and gain insights into their performance. The target audience includes competitive programmers, recruiters, and platform developers.

## ✨ Features

- **Multi-Platform Integration:**
    - LeetCode
    - CodeChef
    - Codeforces

- **User Data Retrieval:**
    - Fetch user profiles from integrated platforms.
    - Access contest history and performance data.
    - Retrieve recent submissions and coding activity.

- **Smart Caching with Redis:**
    - Leverages Redis to cache frequently accessed data, improving response times and reducing load on external APIs. Configurable cache expiration policies are implemented for different data types to ensure data freshness.

- **Rate Limiting:**
    - Implements rate limiting using Bucket4j to prevent abuse and ensure fair usage of the service.

- **Centralized API Documentation:**
    - Uses Swagger to provide interactive API documentation, making it easy for developers to understand and use the service.

- **Customizable Buffering:**
    - WebClient and RestTemplate are configured to support larger buffer sizes for handling large API responses from integrated platforms.

## 🏛️ Architecture

CodePing-Server follows a layered architecture, with distinct layers for controllers, services, mappers, and data models. The architecture emphasizes separation of concerns and promotes modularity and maintainability.

- **Controllers:** Expose REST API endpoints for interacting with the service. They handle incoming requests, delegate to services, and return responses. (e.g., `CPUsersController`, `CodeChefController`)
- **Services:** Contain the business logic for interacting with external platforms, processing data, and managing caching. (e.g., `CPUsersService`, `CodeChefService`, `CodeforcesService`, `LeetCodeService`)
- **Mappers:** Responsible for mapping data between the external platform API responses and the internal data models. (e.g., `CodeChefMapper`, `CodeforcesMapper`, `LeetCodeMapper`)
- **Models:** Represent the data structures used throughout the application. (e.g., `UserProfile`, `ContestHistory`, `Submission`, `CPUsers`)
- **Configuration:** Includes various configuration classes to setup WebClient, RestTemplate, Redis, and OpenAPI. (e.g., `WebClientConfig`, `RestTemplateConfig`, `RedisConfig`, `OpenApiConfig`)

The application uses Spring's dependency injection to manage dependencies between components. The data flow typically involves a controller receiving a request, delegating to a service, the service using a mapper to transform data from an external API, and returning the processed data to the controller.

The architecture promotes testability by allowing individual components to be tested in isolation.

## ⚙️ Installation

Follow these steps to set up and run CodePing-Server:

### Prerequisites

Before you begin, ensure you have the following installed:

- **Java Development Kit (JDK):** Version 17 or higher.
    ```bash
    java -version
    ```
- **Maven:** Version 3.6.0 or higher.
    ```bash
    mvn -version
    ```
- **Redis:** Make sure Redis server is up and running. The server configuration is set to `localhost:6379` by default.
- **Local CodeChef Microservice:** A local CodeChef microservice is required, running on port `8800`. This server needs to be set up separately. Ensure it is running before starting `CodePing-Server`.

### Step-by-Step Installation

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/gowtham-2oo5/CodePing-Server.git
    cd CodePing-Server
    ```

2.  **Build the Project:**

    ```bash
    mvn clean install
    ```

3.  **Run the Application:**

    ```bash
    mvn spring-boot:run
    ```

    Alternatively, you can package the application into an executable JAR file and run it:

    ```bash
    mvn package
    java -jar target/Core-Server-0.0.1-SNAPSHOT.jar
    ```

4.  **Access the Application:**

    The application will start on port 8080. Open your web browser and navigate to `http://localhost:8080/` to see the "Hello World" message.

5.  **Access Swagger UI:**

    The API documentation is available through Swagger UI. Access it by navigating to `http://localhost:8080/swagger-ui/index.html`.

## 🔗 API Endpoints

Here are some of the key API endpoints provided by CodePing-Server:

-   **User Management:**
    -   `POST /api/v1/users`: Create a new user.
    -   `PUT /api/v1/users/{id}`: Update an existing user.
    -   `DELETE /api/v1/users/{id}`: Delete a user.
    -   `GET /api/v1/users/{id}`: Get user by ID.

-   **CodeChef Integration:**
    -   `GET /api/codechef/profile/{username}`: Get CodeChef profile.
    -   `GET /api/codechef/ratings/{username}`: Get CodeChef ratings graph.
    -   `GET /api/codechef/recent-submissions/{username}`: Get recent CodeChef submissions.

-   **Codeforces Integration:**
    -   `GET /api/codeforces/profile/{handle}`: Get Codeforces user profile.
    -   `GET /api/codeforces/rating/{handle}`: Get Codeforces user rating history.
    -   `GET /api/codeforces/recent-submissions/{handle}`: Get recent Codeforces submissions.

-   **LeetCode Integration:**
    -   `GET /api/leetcode/profile/{username}`: Get LeetCode profile.
    -   `GET /api/leetcode/contest-history/{username}`: Get LeetCode contest history.
    -   `GET /api/leetcode/recent-submissions/{username}`: Get recent LeetCode submissions.

## 🛠️ Configuration

The application can be configured using environment variables or by modifying the `application.properties` or `application.yml` file.

Key configuration options include:

-   **Redis Configuration:**
    -   `spring.data.redis.host`: Redis server host (default: `localhost`).
    -   `spring.data.redis.port`: Redis server port (default: `6379`).

-   **Cache Expiration:**
    The expiration times for different caches are defined in `RedisConfig.java`.

    ```java
    // RedisConfig.java
    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory connectionFactory) {
        // Default cache configuration with 7 days expiration
        RedisCacheConfiguration defaultConfig = RedisCacheConfiguration.defaultCacheConfig()
                        .entryTtl(Duration.ofDays(7))
                        // ... other configurations
        // ...
    }
    ```

-   **WebClient Base URLs:**
    The base URLs for the integrated platforms are defined in `WebClientConfig.java`.
        ```java
    // WebClientConfig.java
    @Bean("codeChefWebClient")
    public WebClient codeChefWebClient(ClientCodecConfigurer clientCodecConfigurer) {
        // ...
        return WebClient.builder()
                .baseUrl("http://localhost:8800")
                // ...
                .build();
    }
    ```

## ✅ Testing

The project includes unit tests to ensure the correctness of the code. To run the tests, use the following command:

```bash
mvn test
```

This command will execute all the tests in the `src/test/java` directory.

## ❓ Troubleshooting

-   **Connection Refused to Redis:**
    -   Ensure that the Redis server is running and accessible on the configured host and port.
    -   Verify the Redis configuration in `application.properties` or `application.yml`.

-   **Local CodeChef Microservice Not Running:**
    -   Ensure that the local CodeChef microservice is up and running on `http://localhost:8800`.

-   **API Request Rate Limits Exceeded:**
    -   If you encounter rate limit errors, consider implementing a retry mechanism with exponential backoff. The CodePing-Server uses Bucket4j for rate limiting.

-   **Data Mapping Errors:**
    -   If the application fails to retrieve or map data from an external platform, check the corresponding mapper class for any errors. Examine the external API response and ensure that the mapper is correctly parsing the data.

## 🤝 Contributing

We welcome contributions to CodePing-Server! To contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Implement your changes.
4.  Write tests to ensure the correctness of your changes.
5.  Submit a pull request.

Please ensure that your code adheres to the project's coding standards and includes appropriate documentation.

---

## 🎉 Conclusion

CodePing-Server centralizes competitive programming data, simplifies performance tracking, and helps developers efficiently manage their coding profiles. This project, built with Spring Boot, Redis, and Swagger, empowers users with valuable insights and streamlined access to their progress across multiple platforms.

### 🌟 What's Next?
- [ ] Implement comprehensive error handling and logging.
- [ ] Enhance caching strategies for improved performance.
- [ ] Add support for more competitive programming platforms.
- [ ] Integrate AI-powered code review and performance analysis features.

### 🤝 Contributing
We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### 📞 Support & Contact
- 🐛 Issues: Report bugs via GitHub Issues
- 💬 Questions: Open a discussion or issue

---

<div align="center">
  <strong>⭐ Star this repo if you find it helpful!</strong>
  <br>
  <em>Made with ❤️ for the developer community</em>
</div>
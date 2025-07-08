# CodePing-Server
================
## Project Description
The CodePing-Server is a Spring Boot backend service designed to aggregate and manage competitive programming data from various online judges. It serves as a central hub for user profiles, contest history, and submissions across multiple platforms, including LeetCode, Codeforces, and a local CodeChef microservice.

## Features
*   Internal user management via RESTful API
*   Competitive programming data aggregation from LeetCode, Codeforces, and CodeChef
*   Robustness and performance enhancements through Redis caching and rate limiting
*   Scheduled operations for data synchronization and maintenance
*   Profile sharing functionality for aggregated user performance profiles

## Tech Stack
*   **Backend Framework:** Java 17, Spring Boot 3.x (Spring Web, Spring WebFlux, Spring Data JPA)
*   **Data Persistence:** JPA for relational database interaction
*   **Caching:** Redis (Spring Data Redis)
*   **API Documentation:** OpenAPI 3 (Swagger UI)
*   **External API Integration:** LeetCode, Codeforces, CodeChef (local microservice)
*   **Rate Limiting:** Bucket4j
*   **Utilities:** Lombok, Project Reactor
*   **AI Integration:** Spring AI
*   **Build Tool:** Maven

## Getting Started
### Prerequisites
*   Java 17+
*   Maven
*   Running Redis instance
*   Local CodeChef microservice (for full functionality)
*   API keys for LeetCode, Codeforces, and CodeChef (if required)

### Configuration
Configure database connection properties in `application.properties` or `application.yml`. Set up API keys for external services using environment variables or `application.properties`.

### Installation
Run the following command to build the project:
```bash
mvn clean install
```
### Running
Start the application using the standard Spring Boot run command:
```bash
mvn spring-boot:run
```
Access the Swagger UI for API documentation at `http://localhost:8080/swagger-ui.html`.

## API Endpoints Overview
The API provides endpoints for user management, competitive programming data aggregation, and profile sharing. Refer to the Swagger UI for detailed documentation.

## Database Schema
The database schema consists of entities for users, profiles, contest history, and submissions. The schema is designed to support efficient data retrieval and storage.

## Error Handling
The application implements global exception handling using `GlobalExceptionHandler` to handle various error scenarios.

## Contributing
Contributions are welcome. Please submit a pull request with your changes and a brief description of the updates.

## License
The CodePing-Server is licensed under [insert license].
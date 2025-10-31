package com.scalesec.vulnado;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/demo")
public class SQLInjectionDemoController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private CommentRepository commentRepository;

    /**
     * Endpoint para demostrar vulnerabilidades de SQL injection
     * Ejemplos de payloads maliciosos:
     * 
     * 1. Para /api/demo/users/search?term=admin' OR '1'='1
     * 2. Para /api/demo/users/search?term=admin'; DROP TABLE comments; --
     * 3. Para /api/demo/users/search?term=' UNION SELECT user_id, password,
     * username FROM users --
     */
    @GetMapping("/users/search")
    public ResponseEntity<Map<String, Object>> demonstrateUserSearch(@RequestParam String term) {
        Map<String, Object> response = new HashMap<>();

        try {
            // Esta consulta es vulnerable - el parámetro se inyecta directamente
            List<User> users = userRepository.searchUsersByNameVulnerable(term);
            response.put("success", true);
            response.put("users", users);
            response.put("count", users.size());
            response.put("query_executed",
                    "SELECT * FROM users WHERE username LIKE '%" + term + "%' ORDER BY username");
            response.put("vulnerability", "SQL Injection via LIKE clause with string concatenation");
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            response.put("vulnerability_exploited", true);
        }

        return ResponseEntity.ok(response);
    }

    /**
     * Endpoint para demostrar UNION-based SQL injection
     * Ejemplos de payloads:
     * 
     * 1. username=admin&fakeUser=' UNION SELECT password FROM users WHERE
     * username='admin' --&fakePassword=hacked
     * 2. username=admin&fakeUser=' UNION SELECT user_id FROM users
     * --&fakePassword=''
     */
    @GetMapping("/users/union-demo")
    public ResponseEntity<Map<String, Object>> demonstrateUnionInjection(
            @RequestParam String username,
            @RequestParam String fakeUser,
            @RequestParam String fakePassword) {

        Map<String, Object> response = new HashMap<>();

        try {
            List<Object[]> results = userRepository.getUserWithUnionVulnerable(username, fakeUser, fakePassword);
            response.put("success", true);
            response.put("results", results);
            response.put("query_executed",
                    "SELECT username, password FROM users WHERE username = '" + username +
                            "' UNION SELECT '" + fakeUser + "' as username, '" + fakePassword + "' as password");
            response.put("vulnerability", "UNION-based SQL Injection");
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            response.put("vulnerability_exploited", true);
        }

        return ResponseEntity.ok(response);
    }

    /**
     * Endpoint para demostrar inyección en ORDER BY clause
     * Ejemplos de payloads:
     * 
     * 1. orderBy=username; DROP TABLE comments; --
     * 2. orderBy=(SELECT CASE WHEN (SELECT COUNT(*) FROM users) > 0 THEN username
     * ELSE password END)
     * 3. orderBy=username DESC; UPDATE users SET password='hacked' WHERE
     * username='admin'; --
     */
    @GetMapping("/users/order-demo")
    public ResponseEntity<Map<String, Object>> demonstrateOrderByInjection(
            @RequestParam String since,
            @RequestParam String orderBy) {

        Map<String, Object> response = new HashMap<>();

        try {
            List<User> users = userRepository.findActiveUsersVulnerable(since, orderBy);
            response.put("success", true);
            response.put("users", users);
            response.put("query_executed",
                    "SELECT * FROM users WHERE last_login > '" + since + "' ORDER BY " + orderBy);
            response.put("vulnerability", "SQL Injection in ORDER BY clause");
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            response.put("vulnerability_exploited", true);
        }

        return ResponseEntity.ok(response);
    }

    /**
     * Endpoint para demostrar inyección en WHERE con múltiples condiciones
     * Ejemplos de payloads:
     * 
     * 1. condition=1=1) OR (SELECT COUNT(*) FROM users WHERE password LIKE
     * '%admin%') > 0 --
     * 2. condition=1=1) UNION SELECT COUNT(*) FROM information_schema.tables --
     */
    @GetMapping("/comments/condition-demo")
    public ResponseEntity<Map<String, Object>> demonstrateConditionInjection(@RequestParam String condition) {
        Map<String, Object> response = new HashMap<>();

        try {
            Object[] stats = commentRepository.getCommentStatsVulnerable(condition);
            response.put("success", true);
            response.put("stats", stats);
            response.put("query_executed",
                    "SELECT COUNT(*) as total, MAX(created_on) as latest_comment FROM comments WHERE " + condition);
            response.put("vulnerability", "SQL Injection in WHERE clause condition");
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            response.put("vulnerability_exploited", true);
        }

        return ResponseEntity.ok(response);
    }

    /**
     * Endpoint para demostrar inyección en subconsultas
     * Ejemplos de payloads:
     * 
     * 1. userCondition=username='admin') OR (SELECT COUNT(*) FROM comments) > 0 --
     * 2. userCondition=1=1) UNION SELECT password FROM users WHERE username='admin'
     * --
     */
    @GetMapping("/comments/subquery-demo")
    public ResponseEntity<Map<String, Object>> demonstrateSubqueryInjection(@RequestParam String userCondition) {
        Map<String, Object> response = new HashMap<>();

        try {
            List<Comment> comments = commentRepository.findCommentsByUserConditionVulnerable(userCondition);
            response.put("success", true);
            response.put("comments", comments);
            response.put("query_executed",
                    "SELECT c.* FROM comments c WHERE c.username IN " +
                            "(SELECT u.username FROM users u WHERE " + userCondition + ") ORDER BY c.created_on DESC");
            response.put("vulnerability", "SQL Injection in subquery");
        } catch (Exception e) {
            response.put("success", false);
            response.put("error", e.getMessage());
            response.put("vulnerability_exploited", true);
        }

        return ResponseEntity.ok(response);
    }

    /**
     * Endpoint de información sobre vulnerabilidades presentes
     */
    @GetMapping("/vulnerabilities")
    public ResponseEntity<Map<String, Object>> getVulnerabilityInfo() {
        Map<String, Object> response = new HashMap<>();

        response.put("application", "Vulnado - Vulnerable Spring Boot Application");
        response.put("vulnerabilities_count", 15);

        Map<String, Object> sqlInjectionVulns = new HashMap<>();
        sqlInjectionVulns.put("user_search", "/api/demo/users/search?term=PAYLOAD");
        sqlInjectionVulns.put("union_injection",
                "/api/demo/users/union-demo?username=admin&fakeUser=PAYLOAD&fakePassword=test");
        sqlInjectionVulns.put("order_by_injection", "/api/demo/users/order-demo?since=2023-01-01&orderBy=PAYLOAD");
        sqlInjectionVulns.put("condition_injection", "/api/demo/comments/condition-demo?condition=PAYLOAD");
        sqlInjectionVulns.put("subquery_injection", "/api/demo/comments/subquery-demo?userCondition=PAYLOAD");

        response.put("sql_injection_endpoints", sqlInjectionVulns);

        Map<String, String> examplePayloads = new HashMap<>();
        examplePayloads.put("basic_or", "admin' OR '1'='1");
        examplePayloads.put("union_select", "' UNION SELECT user_id, password, username FROM users --");
        examplePayloads.put("comment_out", "admin'; DROP TABLE comments; --");
        examplePayloads.put("blind_boolean", "admin' AND (SELECT COUNT(*) FROM users) > 0 --");
        examplePayloads.put("time_based", "admin'; WAITFOR DELAY '00:00:05' --");

        response.put("example_payloads", examplePayloads);

        return ResponseEntity.ok(response);
    }
}
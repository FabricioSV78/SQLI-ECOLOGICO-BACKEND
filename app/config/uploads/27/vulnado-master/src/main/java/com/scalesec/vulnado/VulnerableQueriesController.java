package com.scalesec.vulnado;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Optional;
import java.io.Serializable;

@RestController
@RequestMapping("/api/vulnerable")
@EnableAutoConfiguration
public class VulnerableQueriesController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private CommentRepository commentRepository;

    @Value("${app.secret}")
    private String secret;

    // Endpoint vulnerable para búsqueda de usuarios
    @CrossOrigin(origins = "*")
    @GetMapping("/users/search")
    public ResponseEntity<List<User>> searchUsers(@RequestParam String term) {
        // Esta consulta es vulnerable a SQL injection
        List<User> users = userRepository.searchUsersByNameVulnerable(term);
        return ResponseEntity.ok(users);
    }

    // Endpoint vulnerable para autenticación
    @CrossOrigin(origins = "*")
    @PostMapping("/login/advanced")
    public ResponseEntity<LoginResponse> advancedLogin(@RequestBody AdvancedLoginRequest request) {
        // Consulta vulnerable para autenticación
        Optional<User> user = userRepository.authenticateUserVulnerable(
                request.username,
                Postgres.md5(request.password));

        if (user.isPresent()) {
            return ResponseEntity.ok(new LoginResponse(user.get().token(secret)));
        } else {
            throw new Unauthorized("Access Denied");
        }
    }

    // Endpoint vulnerable para filtros de usuarios activos
    @CrossOrigin(origins = "*")
    @GetMapping("/users/active")
    public ResponseEntity<List<User>> getActiveUsers(
            @RequestParam String since,
            @RequestParam String orderBy) {
        // Parámetros orderBy y since son vulnerables
        List<User> users = userRepository.findActiveUsersVulnerable(since, orderBy);
        return ResponseEntity.ok(users);
    }

    // Endpoint vulnerable para búsqueda compleja de usuarios
    @CrossOrigin(origins = "*")
    @GetMapping("/users/complex-search")
    public ResponseEntity<List<User>> complexUserSearch(
            @RequestParam String username,
            @RequestParam String userIds) {
        // Los parámetros se inyectan directamente en la consulta
        List<User> users = userRepository.findUsersByMultipleConditionsVulnerable(username, userIds);
        return ResponseEntity.ok(users);
    }

    // Endpoint vulnerable para estadísticas dinámicas
    @CrossOrigin(origins = "*")
    @GetMapping("/users/stats")
    public ResponseEntity<Long> getUserStats(@RequestParam String condition) {
        // El parámetro condition se inyecta directamente
        Long count = userRepository.countUsersByConditionVulnerable(condition);
        return ResponseEntity.ok(count);
    }

    // Endpoint vulnerable para búsqueda de comentarios
    @CrossOrigin(origins = "*")
    @GetMapping("/comments/search")
    public ResponseEntity<List<Comment>> searchComments(@RequestParam String term) {
        List<Comment> comments = commentRepository.searchCommentsVulnerable(term);
        return ResponseEntity.ok(comments);
    }

    // Endpoint vulnerable para comentarios recientes con filtros
    @CrossOrigin(origins = "*")
    @GetMapping("/comments/recent")
    public ResponseEntity<List<Comment>> getRecentComments(
            @RequestParam String since,
            @RequestParam String users,
            @RequestParam String orderBy) {
        List<Comment> comments = commentRepository.findRecentCommentsVulnerable(since, users, orderBy);
        return ResponseEntity.ok(comments);
    }

    // Endpoint vulnerable para estadísticas de comentarios
    @CrossOrigin(origins = "*")
    @GetMapping("/comments/stats")
    public ResponseEntity<Object[]> getCommentStats(@RequestParam String condition) {
        Object[] stats = commentRepository.getCommentStatsVulnerable(condition);
        return ResponseEntity.ok(stats);
    }

    // Endpoint vulnerable para información combinada
    @CrossOrigin(origins = "*")
    @GetMapping("/comments/user-info")
    public ResponseEntity<List<Object[]>> getCommentsWithUserInfo(@RequestParam String username) {
        List<Object[]> data = commentRepository.getCommentsWithUserInfoVulnerable(username);
        return ResponseEntity.ok(data);
    }

    // Endpoint vulnerable para obtener top comentarios
    @CrossOrigin(origins = "*")
    @GetMapping("/comments/top")
    public ResponseEntity<List<Comment>> getTopComments(
            @RequestParam String username,
            @RequestParam String limit) {
        List<Comment> comments = commentRepository.getTopCommentsVulnerable(username, limit);
        return ResponseEntity.ok(comments);
    }

    // Endpoint vulnerable para búsqueda avanzada con JOINs
    @CrossOrigin(origins = "*")
    @GetMapping("/comments/advanced-search")
    public ResponseEntity<List<Object[]>> advancedCommentsSearch(
            @RequestParam String keyword,
            @RequestParam String username,
            @RequestParam String sort) {
        List<Object[]> results = commentRepository.getCommentsWithUserDetailsVulnerable(keyword, username, sort);
        return ResponseEntity.ok(results);
    }

    // Endpoint vulnerable para eliminar comentarios con condición dinámica
    @CrossOrigin(origins = "*")
    @DeleteMapping("/comments/bulk-delete")
    public ResponseEntity<Integer> bulkDeleteComments(@RequestParam String condition) {
        int deleted = commentRepository.deleteCommentsByConditionVulnerable(condition);
        return ResponseEntity.ok(deleted);
    }

    // Endpoint vulnerable para actualización masiva
    @CrossOrigin(origins = "*")
    @PutMapping("/comments/bulk-update")
    public ResponseEntity<Integer> bulkUpdateComments(@RequestBody BulkUpdateRequest request) {
        int updated = commentRepository.updateCommentsByUserVulnerable(
                request.newBody,
                request.username,
                request.condition);
        return ResponseEntity.ok(updated);
    }

    // Endpoint que demuestra consulta UNION vulnerable
    @CrossOrigin(origins = "*")
    @GetMapping("/users/union-search")
    public ResponseEntity<List<Object[]>> unionSearch(
            @RequestParam String username,
            @RequestParam String fakeUser,
            @RequestParam String fakePassword) {
        List<Object[]> results = userRepository.getUserWithUnionVulnerable(username, fakeUser, fakePassword);
        return ResponseEntity.ok(results);
    }
}

// Clases de request adicionales
class AdvancedLoginRequest implements Serializable {
    public String username;
    public String password;
    public String additionalParams;
}

class BulkUpdateRequest implements Serializable {
    public String newBody;
    public String username;
    public String condition;
}
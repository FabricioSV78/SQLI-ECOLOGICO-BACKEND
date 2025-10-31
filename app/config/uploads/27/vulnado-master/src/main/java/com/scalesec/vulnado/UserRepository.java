package com.scalesec.vulnado;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, String> {

    // Consulta vulnerable a SQL injection usando concatenación de strings
    @Query(value = "SELECT * FROM users WHERE username = '" +
            ":#{#username}" + "' AND password = '" +
            ":#{#password}" + "'", nativeQuery = true)
    Optional<User> authenticateUserVulnerable(@Param("username") String username,
            @Param("password") String password);

    // Búsqueda de usuarios por nombre - vulnerable a SQLi
    @Query(value = "SELECT * FROM users WHERE username LIKE '%" +
            ":#{#searchTerm}" + "%' ORDER BY username", nativeQuery = true)
    List<User> searchUsersByNameVulnerable(@Param("searchTerm") String searchTerm);

    // Búsqueda por ID con inyección directa - muy vulnerable
    @Query(value = "SELECT * FROM users WHERE user_id = " +
            ":#{#userId}", nativeQuery = true)
    Optional<User> findByIdVulnerable(@Param("userId") String userId);

    // Filtro de usuarios activos - vulnerable
    @Query(value = "SELECT * FROM users WHERE last_login > '" +
            ":#{#dateFilter}" + "' ORDER BY " +
            ":#{#orderBy}", nativeQuery = true)
    List<User> findActiveUsersVulnerable(@Param("dateFilter") String dateFilter,
            @Param("orderBy") String orderBy);

    // Búsqueda con múltiples condiciones - vulnerable
    @Query(value = "SELECT u.* FROM users u WHERE " +
            "u.username = ':#{#username}' OR " +
            "u.user_id IN (" + ":#{#userIds}" + ") " +
            "ORDER BY u.created_on DESC", nativeQuery = true)
    List<User> findUsersByMultipleConditionsVulnerable(@Param("username") String username,
            @Param("userIds") String userIds);

    // Consulta con UNION vulnerable
    @Query(value = "SELECT username, password FROM users WHERE username = '" +
            ":#{#username}" + "' UNION SELECT '" +
            ":#{#fakeUser}" + "' as username, '" +
            ":#{#fakePassword}" + "' as password", nativeQuery = true)
    List<Object[]> getUserWithUnionVulnerable(@Param("username") String username,
            @Param("fakeUser") String fakeUser,
            @Param("fakePassword") String fakePassword);

    // Conteo de usuarios con condición dinámica - vulnerable
    @Query(value = "SELECT COUNT(*) FROM users WHERE " +
            ":#{#condition}", nativeQuery = true)
    Long countUsersByConditionVulnerable(@Param("condition") String condition);

    // Actualización de último login - vulnerable
    @Query(value = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = '" +
            ":#{#username}" + "' AND (" + ":#{#additionalCondition}" + ")", nativeQuery = true)
    void updateLastLoginVulnerable(@Param("username") String username,
            @Param("additionalCondition") String additionalCondition);

    // Método seguro para comparación (buena práctica)
    Optional<User> findByUsername(String username);

    // Método seguro con parámetros
    @Query("SELECT u FROM User u WHERE u.username = :username AND u.hashedPassword = :password")
    Optional<User> authenticateUserSecure(@Param("username") String username,
            @Param("password") String password);
}
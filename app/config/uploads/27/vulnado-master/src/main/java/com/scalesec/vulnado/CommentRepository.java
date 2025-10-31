package com.scalesec.vulnado;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface CommentRepository extends JpaRepository<Comment, String> {

    // Búsqueda de comentarios por usuario - vulnerable a SQLi
    @Query(value = "SELECT * FROM comments WHERE username = '" +
            ":#{#username}" + "' ORDER BY created_on DESC", nativeQuery = true)
    List<Comment> findCommentsByUserVulnerable(@Param("username") String username);

    // Búsqueda de comentarios por contenido - vulnerable
    @Query(value = "SELECT * FROM comments WHERE body LIKE '%" +
            ":#{#searchTerm}" + "%' ORDER BY created_on DESC", nativeQuery = true)
    List<Comment> searchCommentsVulnerable(@Param("searchTerm") String searchTerm);

    // Filtro de comentarios por fecha - vulnerable
    @Query(value = "SELECT c.* FROM comments c WHERE c.created_on > '" +
            ":#{#dateFilter}" + "' AND c.username IN (" +
            ":#{#userList}" + ") ORDER BY " +
            ":#{#orderBy}", nativeQuery = true)
    List<Comment> findRecentCommentsVulnerable(@Param("dateFilter") String dateFilter,
            @Param("userList") String userList,
            @Param("orderBy") String orderBy);

    // Estadísticas de comentarios - vulnerable
    @Query(value = "SELECT COUNT(*) as total, " +
            "MAX(created_on) as latest_comment " +
            "FROM comments WHERE " +
            ":#{#condition}", nativeQuery = true)
    Object[] getCommentStatsVulnerable(@Param("condition") String condition);

    // Búsqueda con UNION para obtener información adicional - vulnerable
    @Query(value = "SELECT id, username, body, created_on FROM comments WHERE username = '" +
            ":#{#username}" + "' UNION ALL " +
            "SELECT user_id as id, username, 'USER_INFO' as body, created_on " +
            "FROM users WHERE username = '" +
            ":#{#username}" + "'", nativeQuery = true)
    List<Object[]> getCommentsWithUserInfoVulnerable(@Param("username") String username);

    // Eliminación de comentarios con condición dinámica - vulnerable
    @Modifying
    @Transactional
    @Query(value = "DELETE FROM comments WHERE " +
            ":#{#deleteCondition}", nativeQuery = true)
    int deleteCommentsByConditionVulnerable(@Param("deleteCondition") String deleteCondition);

    // Actualización masiva de comentarios - vulnerable
    @Modifying
    @Transactional
    @Query(value = "UPDATE comments SET body = '" +
            ":#{#newBody}" + "' WHERE username = '" +
            ":#{#username}" + "' AND (" +
            ":#{#additionalCondition}" + ")", nativeQuery = true)
    int updateCommentsByUserVulnerable(@Param("newBody") String newBody,
            @Param("username") String username,
            @Param("additionalCondition") String additionalCondition);

    // Búsqueda con subconsulta - vulnerable
    @Query(value = "SELECT c.* FROM comments c WHERE c.username IN " +
            "(SELECT u.username FROM users u WHERE " +
            ":#{#userCondition}" + ") " +
            "ORDER BY c.created_on DESC", nativeQuery = true)
    List<Comment> findCommentsByUserConditionVulnerable(@Param("userCondition") String userCondition);

    // Top comentarios por usuario con límite dinámico - vulnerable
    @Query(value = "SELECT * FROM comments WHERE username = '" +
            ":#{#username}" + "' ORDER BY created_on DESC LIMIT " +
            ":#{#limitCount}", nativeQuery = true)
    List<Comment> getTopCommentsVulnerable(@Param("username") String username,
            @Param("limitCount") String limitCount);

    // Consulta con múltiples JOINs - vulnerable
    @Query(value = "SELECT c.*, u.user_id, u.created_on as user_created " +
            "FROM comments c INNER JOIN users u ON c.username = u.username " +
            "WHERE c.body LIKE '%" + ":#{#keyword}" + "%' " +
            "AND u.username = '" + ":#{#username}" + "' " +
            "ORDER BY " + ":#{#sortOrder}", nativeQuery = true)
    List<Object[]> getCommentsWithUserDetailsVulnerable(@Param("keyword") String keyword,
            @Param("username") String username,
            @Param("sortOrder") String sortOrder);

    // Métodos seguros para comparación
    List<Comment> findByUsername(String username);

    @Query("SELECT c FROM Comment c WHERE c.body LIKE %:searchTerm% ORDER BY c.created_on DESC")
    List<Comment> searchCommentsSecure(@Param("searchTerm") String searchTerm);

    @Query("SELECT c FROM Comment c WHERE c.created_on > :dateFilter ORDER BY c.created_on DESC")
    List<Comment> findRecentCommentsSecure(@Param("dateFilter") LocalDateTime dateFilter);
}
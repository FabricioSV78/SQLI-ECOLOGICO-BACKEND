package com.scalesec.vulnado;

import org.apache.catalina.Server;
import java.sql.*;
import java.util.Date;
import java.util.List;
import java.util.ArrayList;
import java.util.UUID;
import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "comments")
public class Comment {
  @Id
  public String id;

  @Column(name = "username")
  public String username;

  @Column(name = "body", length = 500)
  public String body;

  @Column(name = "created_on")
  public LocalDateTime created_on;

  public Comment() {
  }

  public Comment(String id, String username, String body, LocalDateTime created_on) {
    this.id = id;
    this.username = username;
    this.body = body;
    this.created_on = created_on;
  }

  // Constructor para compatibilidad con código existente
  public Comment(String id, String username, String body, Timestamp created_on) {
    this.id = id;
    this.username = username;
    this.body = body;
    this.created_on = created_on.toLocalDateTime();
  }

  public static Comment create(String username, String body) {
    LocalDateTime now = LocalDateTime.now();
    Comment comment = new Comment(UUID.randomUUID().toString(), username, body, now);
    try {
      if (comment.commit()) {
        return comment;
      } else {
        throw new BadRequest("Unable to save comment");
      }
    } catch (Exception e) {
      throw new ServerError(e.getMessage());
    }
  }

  public static List<Comment> fetch_all() {
    Statement stmt = null;
    List<Comment> comments = new ArrayList<>();
    try {
      Connection cxn = Postgres.connection();
      stmt = cxn.createStatement();

      String query = "select * from comments;";
      ResultSet rs = stmt.executeQuery(query);
      while (rs.next()) {
        String id = rs.getString("id");
        String username = rs.getString("username");
        String body = rs.getString("body");
        Timestamp created_on = rs.getTimestamp("created_on");
        Comment c = new Comment(id, username, body, created_on);
        comments.add(c);
      }
      cxn.close();
    } catch (Exception e) {
      e.printStackTrace();
      System.err.println(e.getClass().getName() + ": " + e.getMessage());
    }
    return comments;
  }

  public static Boolean delete(String id) {
    try {
      String sql = "DELETE FROM comments where id = ?";
      Connection con = Postgres.connection();
      PreparedStatement pStatement = con.prepareStatement(sql);
      pStatement.setString(1, id);
      return 1 == pStatement.executeUpdate();
    } catch (Exception e) {
      e.printStackTrace();
      return false;
    }
  }

  private Boolean commit() throws SQLException {
    String sql = "INSERT INTO comments (id, username, body, created_on) VALUES (?,?,?,?)";
    Connection con = Postgres.connection();
    PreparedStatement pStatement = con.prepareStatement(sql);
    pStatement.setString(1, this.id);
    pStatement.setString(2, this.username);
    pStatement.setString(3, this.body);
    pStatement.setTimestamp(4, Timestamp.valueOf(this.created_on));
    return 1 == pStatement.executeUpdate();
  }
}

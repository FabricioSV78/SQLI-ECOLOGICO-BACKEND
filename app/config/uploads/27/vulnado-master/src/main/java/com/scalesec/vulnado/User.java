package com.scalesec.vulnado;

import java.sql.Connection;
import java.sql.Statement;
import java.sql.ResultSet;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.JwtParser;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import javax.crypto.SecretKey;
import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "users")
public class User {
  @Id
  @Column(name = "user_id")
  public String id;

  @Column(name = "username", unique = true, nullable = false)
  public String username;

  @Column(name = "password", nullable = false)
  public String hashedPassword;

  @Column(name = "created_on")
  public LocalDateTime createdOn;

  @Column(name = "last_login")
  public LocalDateTime lastLogin;

  public User() {
  }

  public User(String id, String username, String hashedPassword) {
    this.id = id;
    this.username = username;
    this.hashedPassword = hashedPassword;
    this.createdOn = LocalDateTime.now();
  }

  public String token(String secret) {
    SecretKey key = Keys.hmacShaKeyFor(secret.getBytes());
    String jws = Jwts.builder().setSubject(this.username).signWith(key).compact();
    return jws;
  }

  public static void assertAuth(String secret, String token) {
    try {
      SecretKey key = Keys.hmacShaKeyFor(secret.getBytes());
      Jwts.parser()
          .setSigningKey(key)
          .parseClaimsJws(token);
    } catch (Exception e) {
      e.printStackTrace();
      throw new Unauthorized(e.getMessage());
    }
  }

  // Método original vulnerable mantenido para compatibilidad
  public static User fetch(String un) {
    Statement stmt = null;
    User user = null;
    try {
      Connection cxn = Postgres.connection();
      stmt = cxn.createStatement();
      System.out.println("Opened database successfully");

      String query = "select * from users where username = '" + un + "' limit 1";
      System.out.println(query);
      ResultSet rs = stmt.executeQuery(query);
      if (rs.next()) {
        String user_id = rs.getString("user_id");
        String username = rs.getString("username");
        String password = rs.getString("password");
        user = new User(user_id, username, password);
      }
      cxn.close();
    } catch (Exception e) {
      e.printStackTrace();
      System.err.println(e.getClass().getName() + ": " + e.getMessage());
    }
    return user;
  }
}

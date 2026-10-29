package com.islsetu.auth.model;

import jakarta.persistence.*;

@Entity
@Table(name = "operator")
public class Operator {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String username;

    // NOTE: plaintext password — demo only, replace with hashing before real deployment
    @Column(nullable = false)
    private String password;

    @Column(nullable = false)
    private String role; // DOCTOR, POLICE, TEACHER

    private String fullName;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }
}
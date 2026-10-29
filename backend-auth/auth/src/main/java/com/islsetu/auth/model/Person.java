package com.islsetu.auth.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "person")
public class Person {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;
    private Integer age;
    private String phone;

    private String role;             // role context: DOCTOR, POLICE, TEACHER, PUBLIC
    private String operatorUsername; // null for PUBLIC

    private LocalDateTime createdAt = LocalDateTime.now();

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Integer getAge() { return age; }
    public void setAge(Integer age) { this.age = age; }
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public String getOperatorUsername() { return operatorUsername; }
    public void setOperatorUsername(String operatorUsername) { this.operatorUsername = operatorUsername; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
package com.islsetu.auth.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "conversation")
public class Conversation {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String operatorUsername;
    private String operatorFullName;
    private String role;           // DOCTOR, POLICE, TEACHER

    private Long personId;
    private String personName;
    private Integer personAge;
    private String personPhone;

    private String direction;      // SIGN_TO_TEXT | TEXT_TO_SIGN
    private String speaker;        // DEAF_MUTE | HEARING

    @Column(length = 1000)
    private String glossText;      // the sign words involved (either direction)

    @Column(length = 2000)
    private String sentenceText;   // the resulting natural-language sentence

    private String language;

    private LocalDateTime timestamp = LocalDateTime.now();

    // getters/setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getOperatorUsername() { return operatorUsername; }
    public void setOperatorUsername(String v) { this.operatorUsername = v; }
    public String getOperatorFullName() { return operatorFullName; }
    public void setOperatorFullName(String v) { this.operatorFullName = v; }
    public String getRole() { return role; }
    public void setRole(String v) { this.role = v; }
    public Long getPersonId() { return personId; }
    public void setPersonId(Long v) { this.personId = v; }
    public String getPersonName() { return personName; }
    public void setPersonName(String v) { this.personName = v; }
    public Integer getPersonAge() { return personAge; }
    public void setPersonAge(Integer v) { this.personAge = v; }
    public String getPersonPhone() { return personPhone; }
    public void setPersonPhone(String v) { this.personPhone = v; }
    public String getDirection() { return direction; }
    public void setDirection(String v) { this.direction = v; }
    public String getSpeaker() { return speaker; }
    public void setSpeaker(String v) { this.speaker = v; }
    public String getGlossText() { return glossText; }
    public void setGlossText(String v) { this.glossText = v; }
    public String getSentenceText() { return sentenceText; }
    public void setSentenceText(String v) { this.sentenceText = v; }
    public String getLanguage() { return language; }
    public void setLanguage(String v) { this.language = v; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime v) { this.timestamp = v; }
}
package com.islsetu.auth.dto;

public class LoginResponse {
    private boolean success;
    private String message;
    private String role;
    private String fullName;

    public LoginResponse(boolean success, String message, String role, String fullName) {
        this.success = success;
        this.message = message;
        this.role = role;
        this.fullName = fullName;
    }
    public boolean isSuccess() { return success; }
    public String getMessage() { return message; }
    public String getRole() { return role; }
    public String getFullName() { return fullName; }
}
package com.islsetu.auth.controller;

import com.islsetu.auth.dto.LoginRequest;
import com.islsetu.auth.dto.LoginResponse;
import com.islsetu.auth.model.Operator;
import com.islsetu.auth.repository.OperatorRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*") // demo-only: restrict to real LAN origin before production
public class AuthController {

    @Autowired
    private OperatorRepository operatorRepository;

    @PostMapping("/login")
    public LoginResponse login(@RequestBody LoginRequest request) {
        Optional<Operator> opt = operatorRepository.findByUsername(request.getUsername());
        if (opt.isPresent() && opt.get().getPassword().equals(request.getPassword())) {
            Operator op = opt.get();
            return new LoginResponse(true, "Login successful", op.getRole(), op.getFullName());
        }
        return new LoginResponse(false, "Invalid username or password", null, null);
    }
}
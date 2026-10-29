package com.islsetu.auth.repository;

import com.islsetu.auth.model.Operator;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface OperatorRepository extends JpaRepository<Operator, Long> {
    Optional<Operator> findByUsername(String username);
}
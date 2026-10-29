package com.islsetu.auth.repository;

import com.islsetu.auth.model.Person;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PersonRepository extends JpaRepository<Person, Long> {
}
package com.islsetu.auth.controller;

import com.islsetu.auth.model.Person;
import com.islsetu.auth.repository.PersonRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/persons")
@CrossOrigin(origins = "*")
public class PersonController {

    @Autowired
    private PersonRepository personRepository;

    @PostMapping
    public Person create(@RequestBody Person person) {
        return personRepository.save(person);
    }

    @GetMapping
    public List<Person> list() {
        return personRepository.findAll();
    }
}
package com.islsetu.auth.controller;

import com.islsetu.auth.model.Conversation;
import com.islsetu.auth.repository.ConversationRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/conversations")
@CrossOrigin(origins = "*")
public class ConversationController {

    @Autowired
    private ConversationRepository conversationRepository;

    @PostMapping
    public Conversation create(@RequestBody Conversation conversation) {
        return conversationRepository.save(conversation);
    }

    // Dashboard: fetch only this operator's own conversation history
    @GetMapping
    public List<Conversation> listByOperator(@RequestParam String operatorUsername) {
        return conversationRepository.findByOperatorUsernameOrderByTimestampDesc(operatorUsername);
    }
}
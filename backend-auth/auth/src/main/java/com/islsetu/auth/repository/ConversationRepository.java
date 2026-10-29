package com.islsetu.auth.repository;

import com.islsetu.auth.model.Conversation;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ConversationRepository extends JpaRepository<Conversation, Long> {
    List<Conversation> findByOperatorUsernameOrderByTimestampDesc(String operatorUsername);
}
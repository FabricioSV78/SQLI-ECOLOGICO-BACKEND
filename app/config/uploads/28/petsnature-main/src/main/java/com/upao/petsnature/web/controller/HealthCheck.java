package com.upao.petsnature.web.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/healthcheck")
@CrossOrigin("*")
@RequiredArgsConstructor
public class HealthCheck {
    @GetMapping
    public ResponseEntity<String> checkHealth() {
        return ResponseEntity.ok("<health>ok</health>");
    }
}

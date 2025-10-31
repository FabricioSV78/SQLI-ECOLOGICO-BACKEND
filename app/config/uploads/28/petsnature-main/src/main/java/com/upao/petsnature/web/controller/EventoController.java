package com.upao.petsnature.web.controller;

import com.upao.petsnature.domain.dto.eventoDto.DatosDetallesEvento;
import com.upao.petsnature.domain.dto.eventoDto.DatosRegistroEvento;
import com.upao.petsnature.domain.entity.Evento;
import com.upao.petsnature.services.EventoService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/evento")
@CrossOrigin("*")
@RequiredArgsConstructor
public class EventoController {
    @Autowired
    private EventoService eventoService;

    @PostMapping("/registrar")
    public ResponseEntity<?> registrarEvento(@RequestBody DatosRegistroEvento datos) {
        try {
            eventoService.registrarEvento(datos);
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            return new ResponseEntity<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}

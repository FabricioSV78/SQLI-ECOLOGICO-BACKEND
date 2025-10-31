package com.upao.petsnature.services;

import com.upao.petsnature.domain.dto.eventoDto.DatosRegistroEvento;

public interface EventoService {
    void registrarEvento(DatosRegistroEvento datos);
}

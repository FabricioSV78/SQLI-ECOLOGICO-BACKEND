package com.upao.petsnature.services;

import com.upao.petsnature.domain.entity.Raza;

import java.util.List;

public interface RazaService {
    Raza crearRaza(Raza raza);
    List<Raza> obtenerTodasLasRazas();
    Raza actualizarRaza(Long id, Raza raza);
    void eliminarRaza(Long id);
}

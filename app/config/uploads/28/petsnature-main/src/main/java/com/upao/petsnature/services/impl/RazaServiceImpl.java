package com.upao.petsnature.services.impl;

import com.upao.petsnature.domain.entity.Raza;
import com.upao.petsnature.infra.repository.RazaRepository;
import com.upao.petsnature.services.RazaService;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RazaServiceImpl implements RazaService {
    @Autowired
    private RazaRepository razaRepository;

    @Override
    public Raza crearRaza(Raza raza) {
        return razaRepository.save(raza);
    }

    @Override
    public List<Raza> obtenerTodasLasRazas() {
        return razaRepository.findAll();
    }

    @Override
    public Raza actualizarRaza(Long id, Raza raza) {
        Raza razaExistente = razaRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Raza no encontrada con ID: " + id));
        razaExistente.setNombre(raza.getNombre());
        return razaRepository.save(razaExistente);
    }

    @Override
    public void eliminarRaza(Long id) {
        if (!razaRepository.existsById(id)) {
            throw new EntityNotFoundException("Raza no encontrada con ID: " + id);
        }
        razaRepository.deleteById(id);
    }

}

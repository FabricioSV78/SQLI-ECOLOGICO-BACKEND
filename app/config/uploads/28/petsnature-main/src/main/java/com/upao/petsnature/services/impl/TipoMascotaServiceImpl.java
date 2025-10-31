package com.upao.petsnature.services.impl;

import com.upao.petsnature.domain.entity.TipoMascota;
import com.upao.petsnature.infra.repository.TipoMascotaRepository;
import com.upao.petsnature.services.TipoMascotaService;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TipoMascotaServiceImpl implements TipoMascotaService {
    @Autowired
    private TipoMascotaRepository tipoMascotaRepository;

    @Override
    public TipoMascota crearTipoMascota(TipoMascota tipoMascota) {
        return tipoMascotaRepository.save(tipoMascota);
    }

    @Override
    public List<TipoMascota> obtenerTodosLosTiposMascota() {
        return tipoMascotaRepository.findAll();
    }

    @Override
    public TipoMascota actualizarTipoMascota(Long id, TipoMascota tipoMascota) {
        TipoMascota tipoMascotaExistente = tipoMascotaRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Tipo de mascota no encontrado con ID: " + id));
        tipoMascotaExistente.setNombre(tipoMascota.getNombre());
        return tipoMascotaRepository.save(tipoMascotaExistente);
    }

    @Override
    public void eliminarTipoMascota(Long id) {
        if (!tipoMascotaRepository.existsById(id)) {
            throw new EntityNotFoundException("Tipo de mascota no encontrado con ID: " + id);
        }
        tipoMascotaRepository.deleteById(id);
    }

}

package com.upao.petsnature.services;

import com.upao.petsnature.domain.entity.Raza;
import com.upao.petsnature.domain.entity.TipoMascota;

import java.util.List;

public interface TipoMascotaService {
    TipoMascota crearTipoMascota(TipoMascota tipoMascota);
    List<TipoMascota> obtenerTodosLosTiposMascota();
    TipoMascota actualizarTipoMascota(Long id, TipoMascota tipoMascota);
    void eliminarTipoMascota(Long id);
}

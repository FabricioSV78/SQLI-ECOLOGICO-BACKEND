package com.upao.petsnature.domain.dto.mascotaDto;

import com.upao.petsnature.domain.entity.Mascota;

public record DatosDetallesMascota(
    String nombreMascota,
    String fotoMascota,
    String fechaNacimiento,
    float peso,
    String alimentacion,
    String color,
    String detalles,
    String raza
) {
    public DatosDetallesMascota(Mascota mascota){
        this(mascota.getNombre(), mascota.getFoto(), mascota.getFecha().toString(),
                mascota.getPeso(), mascota.getAlimentacion(), mascota.getColor(), mascota.getDetalles(),
                mascota.getRaza().getNombre());
    }
}

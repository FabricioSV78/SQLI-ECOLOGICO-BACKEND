package com.upao.petsnature.domain.dto.mascotaDto;

import java.time.LocalDate;

public record DatosActualizarMascota(
    String nombreMascota,
    String fotoMascota,
    LocalDate fechaNacimiento,
    Float peso,
    String alimentacion,
    String color,
    String detalles
) {
}

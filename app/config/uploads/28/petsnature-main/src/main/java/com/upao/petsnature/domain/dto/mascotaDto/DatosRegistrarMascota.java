package com.upao.petsnature.domain.dto.mascotaDto;

import jakarta.persistence.Column;
import jakarta.persistence.Lob;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDate;

public record DatosRegistrarMascota(
    @NotBlank String nombreMascota,
    @NotBlank @Lob String fotoMascota,
    @NotBlank LocalDate fechaNacimiento,
    @NotNull float peso,
    @NotBlank String alimentacion,
    @NotBlank String color,
    String detalles,
    @NotNull Long razaId
) {
}

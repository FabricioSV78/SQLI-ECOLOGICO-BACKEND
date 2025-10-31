package com.upao.petsnature.domain.dto.eventoDto;

import java.time.LocalDate;
import java.util.List;

public record DatosRegistroEvento(
        String veterinaria,
        String descripcion,
        String costo,
        String tipoEvento,
        String archivo,
        Long mascotaId,
        String nombreMedicamento,
        String descripcionMedicamento,
        String tipoMedicamento,
        LocalDate fechaMedicamento
) {
}

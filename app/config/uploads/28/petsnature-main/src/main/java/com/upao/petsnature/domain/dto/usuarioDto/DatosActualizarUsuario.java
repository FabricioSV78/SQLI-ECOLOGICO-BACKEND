package com.upao.petsnature.domain.dto.usuarioDto;

public record DatosActualizarUsuario(
    String username,
    String nombre,
    String apellido,
    String telefono,
    String correo,
    String dni
) {
}

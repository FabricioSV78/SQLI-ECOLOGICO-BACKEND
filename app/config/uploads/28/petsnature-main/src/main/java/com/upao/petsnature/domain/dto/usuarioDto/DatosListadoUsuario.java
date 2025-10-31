package com.upao.petsnature.domain.dto.usuarioDto;

import com.upao.petsnature.domain.entity.Usuario;

public record DatosListadoUsuario(
    String username,
    String nombre,
    String apellido,
    String telefono,
    String correo,
    String dni
) {
    public DatosListadoUsuario(Usuario usuario) {
        this(usuario.getUsername(), usuario.getNombre(), usuario.getApellido(),
                usuario.getTelefono(), usuario.getCorreo(), usuario.getDni());
    }
}

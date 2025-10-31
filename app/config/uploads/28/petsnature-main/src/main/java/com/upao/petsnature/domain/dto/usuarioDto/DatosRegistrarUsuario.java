package com.upao.petsnature.domain.dto.usuarioDto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.antlr.v4.runtime.misc.NotNull;
import org.hibernate.validator.constraints.Length;

public record DatosRegistrarUsuario(
        @NotBlank @Length(max = 100) String nombre,
        @NotBlank @Length(max = 100) String apellido,
        @NotNull @Pattern(regexp = "\\d{8}") String dni,
        @NotNull @Size(min = 0, max = 9) String telefono,
        @NotBlank @Email @Length(max = 100) String correo,
        @NotBlank @Length(max = 100) String username,
        @NotBlank @Length(max = 100) String password
) {
}

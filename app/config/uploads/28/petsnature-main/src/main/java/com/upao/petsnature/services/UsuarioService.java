package com.upao.petsnature.services;

import com.upao.petsnature.domain.dto.usuarioDto.DatosRegistrarUsuario;
import com.upao.petsnature.domain.entity.Rol;
import com.upao.petsnature.domain.entity.Usuario;
import com.upao.petsnature.infra.security.LoginRequest;
import com.upao.petsnature.infra.security.TokenResponse;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import java.util.Optional;

public interface UsuarioService {

    TokenResponse login(LoginRequest request);

    TokenResponse addUsuario(DatosRegistrarUsuario usuario);

    Page<Usuario> getAllUsuarios(Pageable pageable);

    Optional<Usuario> getUsuarioById(Long id);

    Usuario obtenerUsuarioAutenticado();

    void cambiarRolUsuario(Long usuarioId, Rol nuevoRol);

    void updateUsuario(Usuario usuario);

    void eliminarUsuario(Usuario usuario);
}

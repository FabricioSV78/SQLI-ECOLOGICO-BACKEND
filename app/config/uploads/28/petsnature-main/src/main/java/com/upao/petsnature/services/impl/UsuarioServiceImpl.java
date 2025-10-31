package com.upao.petsnature.services.impl;

import com.upao.petsnature.domain.dto.usuarioDto.DatosRegistrarUsuario;
import com.upao.petsnature.domain.entity.Rol;
import com.upao.petsnature.domain.entity.Usuario;
import com.upao.petsnature.infra.exception.ValidacionDeIntegridad;
import com.upao.petsnature.infra.repository.UsuarioRepository;
import com.upao.petsnature.infra.security.JwtService;
import com.upao.petsnature.infra.security.LoginRequest;
import com.upao.petsnature.infra.security.TokenResponse;
import com.upao.petsnature.services.UsuarioService;
import jakarta.persistence.EntityNotFoundException;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Optional;

@RequiredArgsConstructor
@Service
public class UsuarioServiceImpl implements UsuarioService {
    private final UsuarioRepository usuarioRepository;
    private final JwtService jwtService;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;

    @Override
    public TokenResponse login(LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getUsername(),
                        request.getPassword()
                )
        );

        SecurityContextHolder.getContext().setAuthentication(authentication);
        Usuario user = usuarioRepository.findByUsername(request.getUsername())
                .orElseThrow(() -> new UsernameNotFoundException("Usuario no encontrado con username: " + request.getUsername()));

        if (!user.isEnabled()) {
            throw new DisabledException("Este usuario ha sido deshabilitado.");
        }

        String token = jwtService.getToken(user, user);
        return TokenResponse.builder()
                .token(token)
                .build();
    }

    @Override
    public TokenResponse addUsuario(DatosRegistrarUsuario datos) {
        Usuario usuario = new Usuario();
        usuario.setNombre(datos.nombre());
        usuario.setApellido(datos.apellido());
        usuario.setDni(datos.dni());
        usuario.setTelefono(datos.telefono());
        usuario.setCorreo(datos.correo());
        usuario.setUsername(datos.username());
        usuario.setPassword(passwordEncoder.encode(datos.password()));
        usuario.setRol(Rol.USER);

        usuarioRepository.save(usuario);

        String token = jwtService.getToken(usuario, usuario);
        return TokenResponse.builder()
                .token(token)
                .build();
    }

    @Override
    public Page<Usuario> getAllUsuarios(Pageable pageable) {
        return usuarioRepository.findAll(pageable);
    }

    @Override
    public Optional<Usuario> getUsuarioById(Long id) {
        return usuarioRepository.findById(id);
    }

    @Override
    public Usuario obtenerUsuarioAutenticado() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication == null || !authentication.isAuthenticated()) {
            throw new RuntimeException("No hay usuario autenticado");
        }

        String currentUserName = authentication.getName();
        return usuarioRepository.findByUsername(currentUserName)
                .orElseThrow(() -> new EntityNotFoundException("Usuario no encontrado"));
    }

    @Transactional
    @Override
    public void cambiarRolUsuario(Long usuarioId, Rol nuevoRol) {
        Usuario usuario = usuarioRepository.findById(usuarioId)
                .orElseThrow(() -> new RuntimeException("Usuario no encontrado"));
        usuario.setRol(nuevoRol);
        usuarioRepository.save(usuario);
    }

    @Transactional
    @Override
    public void updateUsuario(Usuario usuario) {
        validarDatosUsuario(usuario);
        usuarioRepository.save(usuario);
    }

    private void validarDatosUsuario(Usuario usuario) {
        if (usuario.getUsername() == null || usuario.getUsername().isEmpty()) {
            throw new ValidacionDeIntegridad("El username no puede ser vacío");
        }
    }

    @Transactional
    @Override
    public void eliminarUsuario(Usuario usuario) {
        usuario.setEnabled(false);
        usuarioRepository.save(usuario);
    }
}

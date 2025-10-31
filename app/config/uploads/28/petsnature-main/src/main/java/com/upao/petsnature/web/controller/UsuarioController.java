package com.upao.petsnature.web.controller;

import com.upao.petsnature.domain.dto.usuarioDto.DatosActualizarUsuario;
import com.upao.petsnature.domain.dto.usuarioDto.DatosListadoUsuario;
import com.upao.petsnature.domain.dto.usuarioDto.DatosRegistrarUsuario;
import com.upao.petsnature.domain.entity.Usuario;
import com.upao.petsnature.infra.security.LoginRequest;
import com.upao.petsnature.infra.security.TokenResponse;
import com.upao.petsnature.services.UsuarioService;
import jakarta.transaction.Transactional;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/usuario")
@CrossOrigin("*")
@RequiredArgsConstructor
public class UsuarioController {

    @Autowired
    private UsuarioService usuarioService;

    @PostMapping("/login")
    @Transactional
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        try {
            TokenResponse tokenResponse = usuarioService.login(request);
            return ResponseEntity.ok(tokenResponse);
        } catch (DisabledException ex) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Cuenta deshabilitada.");
        } catch (UsernameNotFoundException ex) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Usuario no encontrado.");
        } catch (AuthenticationException ex) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Error en la autenticación.");
        }
    }

    @PostMapping("/registrar")
    @Transactional
    public ResponseEntity<TokenResponse> addUsuario(@RequestBody @Valid DatosRegistrarUsuario datos) {
        return ResponseEntity.ok(usuarioService.addUsuario(datos));
    }

    @GetMapping("/{id}")
    public Usuario findById(@PathVariable Long id){
        return usuarioService.getUsuarioById(id).orElse(null);
    }

    @GetMapping("/perfil")
    public DatosListadoUsuario obtenerPerfil() {
        Usuario usuario = usuarioService.obtenerUsuarioAutenticado();

        return new DatosListadoUsuario(usuario);
    }

    @DeleteMapping("/perfil/eliminar")
    public ResponseEntity<String> eliminarCuenta() {
        // Obtener al usuario autenticado
        Usuario usuarioAutenticado = usuarioService.obtenerUsuarioAutenticado();

        // Deshabilitar  al usuario autenticado
        usuarioService.eliminarUsuario(usuarioAutenticado);

        return ResponseEntity.ok("Cuenta eliminada exitosamente");
    }

    @PutMapping("/perfil/actualizar")
    @Transactional
    public ResponseEntity<DatosListadoUsuario> actualizarPerfil(@RequestBody @Valid DatosActualizarUsuario datos) {
        Usuario usuarioAutenticado = usuarioService.obtenerUsuarioAutenticado();

        usuarioAutenticado.actualizarUsuario(datos);
        usuarioService.updateUsuario(usuarioAutenticado);

        return ResponseEntity.ok(new DatosListadoUsuario(usuarioAutenticado));
    }
}

package com.upao.petsnature.infra.repository;

import com.upao.petsnature.domain.entity.Usuario;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface UsuarioRepository extends JpaRepository<Usuario, Long> {
    Optional<Usuario> findByUsername(String username);
    

    @Query(value = "SELECT u.* FROM usuarios u WHERE u.email = '" + "?1" + "' OR u.telefono = '" + "?1" + "'", nativeQuery = true)
    List<Usuario> buscarPorEmailOTelefonoVulnerable(String busqueda);
}

package com.upao.petsnature.infra.repository;

import com.upao.petsnature.domain.entity.Raza;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface RazaRepository extends JpaRepository<Raza, Long> {
    
    
    @Query(value = "SELECT r.* FROM razas r WHERE UPPER(r.nombre) LIKE UPPER(CONCAT('%', ?1, '%')) AND r.tipo_mascota_id = ?2", nativeQuery = true)
    List<Raza> buscarRazasSeguro(String nombre, Long tipoMascotaId);
}

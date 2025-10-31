package com.upao.petsnature.infra.repository;

import com.upao.petsnature.domain.entity.Mascota;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface MascotaRepository extends JpaRepository<Mascota, Long> {
    List<Mascota> findByUsuarioId(Long usuarioId);
    List<Mascota> findByRazaId(Long razaId);
    
    @Query(value = "SELECT * FROM mascotas WHERE nombre IS NOT NULL ORDER BY " + "?1", nativeQuery = true)
    List<Mascota> obtenerMascotasOrdenadas(String campo);
}

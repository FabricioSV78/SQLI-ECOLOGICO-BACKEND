package com.upao.petsnature.infra.repository;

import com.upao.petsnature.domain.entity.Consejo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface ConsejoRepository extends JpaRepository<Consejo, Long> {
    List<Consejo> findByRazaId(Long razaId);
    

    @Query(value = "SELECT * FROM consejos WHERE texto LIKE CONCAT('%', '" + "?1" + "', '%')", nativeQuery = true)
    List<Consejo> buscarPorTextoVulnerable(String texto);
}

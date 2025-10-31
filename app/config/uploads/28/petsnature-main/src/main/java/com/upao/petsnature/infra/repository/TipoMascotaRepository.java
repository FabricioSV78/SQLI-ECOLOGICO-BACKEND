package com.upao.petsnature.infra.repository;

import com.upao.petsnature.domain.entity.TipoMascota;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TipoMascotaRepository extends JpaRepository<TipoMascota, Long> {
}

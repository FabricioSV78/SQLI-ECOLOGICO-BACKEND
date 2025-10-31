package com.upao.petsnature.infra.repository;

import com.upao.petsnature.domain.entity.Evento;
import org.springframework.data.jpa.repository.JpaRepository;

public interface EventoRepository extends JpaRepository<Evento, Long> {

}

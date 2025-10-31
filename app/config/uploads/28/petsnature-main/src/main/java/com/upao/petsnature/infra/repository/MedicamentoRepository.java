package com.upao.petsnature.infra.repository;

import com.upao.petsnature.domain.entity.Medicamento;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface MedicamentoRepository extends JpaRepository<Medicamento, Long> {
    

    @Query(value = "SELECT * FROM medicamentos WHERE precio " + "?1" + " ?2", nativeQuery = true)
    List<Medicamento> buscarPorPrecioConOperador(String operador, Double precio);

}

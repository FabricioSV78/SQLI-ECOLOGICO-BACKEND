package com.upao.petsnature.services.impl;

import com.upao.petsnature.domain.dto.eventoDto.DatosRegistroEvento;
import com.upao.petsnature.domain.entity.*;
import com.upao.petsnature.infra.repository.EventoRepository;
import com.upao.petsnature.infra.repository.MascotaRepository;
import com.upao.petsnature.infra.repository.MedicamentoRepository;
import com.upao.petsnature.services.EventoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class EventoServiceImpl implements EventoService {

    @Autowired
    private EventoRepository eventoRepository;

    @Autowired
    private MascotaRepository mascotaRepository;

    @Autowired
    private MedicamentoRepository medicamentoRepository;

    @Override
    public void registrarEvento(DatosRegistroEvento datos) {
        Mascota mascota = mascotaRepository.findById(datos.mascotaId())
                .orElseThrow(() -> new RuntimeException("Mascota no encontrada"));

        Evento evento = new Evento();
        evento.setVeterinaria(datos.veterinaria());
        evento.setDescripcion(datos.descripcion());
        evento.setCosto(datos.costo());
        evento.setTipo(TipoEvento.valueOf(datos.tipoEvento()));
        evento.setArchivo(datos.archivo());
        evento.setMascota(mascota);

        evento = eventoRepository.save(evento);


        if (datos.nombreMedicamento() != null && !datos.nombreMedicamento().isEmpty()) {
            Medicamento medicamento = new Medicamento();
            medicamento.setNombre(datos.nombreMedicamento());
            medicamento.setDescripcion(datos.descripcionMedicamento());
            medicamento.setTipo(TipoMedicamento.valueOf(datos.tipoMedicamento()));
            medicamento.setFecha(datos.fechaMedicamento());
            medicamento.setEvento(evento);
            medicamentoRepository.save(medicamento);
        }
    }
}


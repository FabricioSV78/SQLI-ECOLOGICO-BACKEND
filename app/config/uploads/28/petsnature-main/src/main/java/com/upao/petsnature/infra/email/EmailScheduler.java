package com.upao.petsnature.infra.email;

import com.upao.petsnature.domain.entity.Usuario;
import com.upao.petsnature.infra.repository.UsuarioRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class EmailScheduler {

    @Autowired
    private EmailReminderService emailReminderService;

    @Autowired
    private UsuarioRepository usuarioRepository;

    // Se ejecuta cada lunes, miércoles y sabado a las 11:00 AM
    @Scheduled(cron = "0 0 11 * * MON,WED,SAT")
    public void enviarConsejos() {
        List<Usuario> usuarios = usuarioRepository.findAll();
        for (Usuario usuario : usuarios) {
            usuario.getMascota().forEach(mascota -> {
                if (mascota.getRaza() != null) {
                    emailReminderService.enviarConsejoAMascotaOwner(usuario.getCorreo(), mascota.getRaza().getId());
                }
            });
        }
    }
}

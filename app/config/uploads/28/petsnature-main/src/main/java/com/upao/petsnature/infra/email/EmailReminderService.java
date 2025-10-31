package com.upao.petsnature.infra.email;

import com.upao.petsnature.domain.entity.Consejo;
import com.upao.petsnature.infra.repository.ConsejoRepository;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

@Service
public class EmailReminderService {
    @Autowired
    private JavaMailSender mailSender;

    @Autowired
    private ConsejoRepository consejoRepository;

    public void enviarConsejoAMascotaOwner(String email, Long razaId) {
        List<Consejo> consejos = consejoRepository.findByRazaId(razaId);
        if (!consejos.isEmpty()) {
            // Enviar consejos en un ciclo, uno a uno por cada ejecución
            AtomicInteger index = new AtomicInteger(0);
            int consejoIndex = index.getAndUpdate(i -> (i + 1) % consejos.size());
            Consejo consejo = consejos.get(consejoIndex);

            MimeMessage mensaje = mailSender.createMimeMessage();

            try {
                MimeMessageHelper helper = new MimeMessageHelper(mensaje, MimeMessageHelper.MULTIPART_MODE_MIXED_RELATED, StandardCharsets.UTF_8.name());
                helper.setTo(email);
                helper.setSubject("Consejo para el cuidado de tu mascota");

                String contenido = String.format("Hola,\n\nAquí tienes un consejo para cuidar mejor a tu mascota de la raza: %s\n\n%s\n\nSaludos cordiales,\nEl equipo de PetsNature", consejo.getRaza().getNombre(), consejo.getTexto());
                helper.setText(contenido);

                mailSender.send(mensaje);
            } catch (MessagingException e) {
                e.printStackTrace();
            }
        }
    }
}


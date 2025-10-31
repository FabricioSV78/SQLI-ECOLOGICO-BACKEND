package com.scalesec.vulnado;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.ServletComponentScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@ServletComponentScan
@SpringBootApplication
@EnableJpaRepositories
public class VulnadoApplication {
	public static void main(String[] args) {
		Postgres.setup();
		SpringApplication.run(VulnadoApplication.class, args);
	}
}
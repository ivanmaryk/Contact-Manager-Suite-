// contacts.go - Менеджер контактов на Go (веб-сервер + JSON)
package main

import (
	"encoding/json"
	"fmt"
	"html/template"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

type Contact struct {
	ID        int    `json:"id"`
	FirstName string `json:"firstName"`
	LastName  string `json:"lastName"`
	Phone     string `json:"phone"`
	Email     string `json:"email"`
	Address   string `json:"address"`
	Group     string `json:"group"`
	Notes     string `json:"notes"`
	PhotoURL  string `json:"photoUrl"`
	Created   string `json:"created"`
}

var contacts []Contact
var nextID = 1
const dataFile = "contacts.json"

func loadContacts() {
	file, err := ioutil.ReadFile(dataFile)
	if err != nil {
		contacts = []Contact{}
		nextID = 1
		return
	}
	json.Unmarshal(file, &contacts)
	nextID = 1
	for _, c := range contacts {
		if c.ID >= nextID {
			nextID = c.ID + 1
		}
	}
}

func saveContacts() {
	data, _ := json.MarshalIndent(contacts, "", "  ")
	ioutil.WriteFile(dataFile, data, 0644)
}

func main() {
	loadContacts()
	http.HandleFunc("/", handleIndex)
	http.HandleFunc("/api/contacts", handleContacts)
	http.HandleFunc("/api/contacts/", handleContactById)
	http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("static"))))
	log.Println("Сервер запущен на http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func handleIndex(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("index.html"))
	tmpl.Execute(w, nil)
}

func handleContacts(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	switch r.Method {
	case http.MethodGet:
		group := r.URL.Query().Get("group")
		search := r.URL.Query().Get("search")
		filtered := contacts
		if group != "" && group != "all" {
			tmp := []Contact{}
			for _, c := range filtered {
				if c.Group == group {
					tmp = append(tmp, c)
				}
			}
			filtered = tmp
		}
		if search != "" {
			search = strings.ToLower(search)
			tmp := []Contact{}
			for _, c := range filtered {
				if strings.Contains(strings.ToLower(c.FirstName+c.LastName), search) ||
					strings.Contains(c.Phone, search) ||
					strings.Contains(strings.ToLower(c.Email), search) {
					tmp = append(tmp, c)
				}
			}
			filtered = tmp
		}
		json.NewEncoder(w).Encode(filtered)
	case http.MethodPost:
		var c Contact
		json.NewDecoder(r.Body).Decode(&c)
		c.ID = nextID
		nextID++
		c.Created = time.Now().Format(time.RFC3339)
		contacts = append(contacts, c)
		saveContacts()
		json.NewEncoder(w).Encode(c)
	default:
		w.WriteHeader(http.StatusMethodNotAllowed)
	}
}

func handleContactById(w http.ResponseWriter, r *http.Request) {
	idStr := strings.TrimPrefix(r.URL.Path, "/api/contacts/")
	id, _ := strconv.Atoi(idStr)
	w.Header().Set("Content-Type", "application/json")
	switch r.Method {
	case http.MethodGet:
		for _, c := range contacts {
			if c.ID == id {
				json.NewEncoder(w).Encode(c)
				return
			}
		}
		w.WriteHeader(http.StatusNotFound)
	case http.MethodPut:
		var updated Contact
		json.NewDecoder(r.Body).Decode(&updated)
		for i, c := range contacts {
			if c.ID == id {
				updated.ID = id
				updated.Created = c.Created
				contacts[i] = updated
				saveContacts()
				json.NewEncoder(w).Encode(updated)
				return
			}
		}
		w.WriteHeader(http.StatusNotFound)
	case http.MethodDelete:
		for i, c := range contacts {
			if c.ID == id {
				contacts = append(contacts[:i], contacts[i+1:]...)
				saveContacts()
				w.WriteHeader(http.StatusNoContent)
				return
			}
		}
		w.WriteHeader(http.StatusNotFound)
	default:
		w.WriteHeader(http.StatusMethodNotAllowed)
	}
}
